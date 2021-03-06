import contextlib

from django.db import transaction
from django.db.models import Manager
from django.db.models import Q
from django_cte import CTEQuerySet
from mptt.managers import TreeManager

from contentcuration.db.models.query import CustomTreeQuerySet


class CustomManager(Manager.from_queryset(CTEQuerySet)):
    """
    The CTEManager improperly overrides `get_queryset`
    """

    pass


class CustomContentNodeTreeManager(TreeManager.from_queryset(CustomTreeQuerySet)):
    # Added 7-31-2018. We can remove this once we are certain we have eliminated all cases
    # where root nodes are getting prepended rather than appended to the tree list.
    def _create_tree_space(self, target_tree_id, num_trees=1):
        """
        Creates space for a new tree by incrementing all tree ids
        greater than ``target_tree_id``.
        """

        if target_tree_id == -1:
            raise Exception(
                "ERROR: Calling _create_tree_space with -1! Something is attempting to sort all MPTT trees root nodes!"
            )

        return super(CustomContentNodeTreeManager, self)._create_tree_space(
            target_tree_id, num_trees
        )

    def _get_next_tree_id(self, *args, **kwargs):
        from contentcuration.models import MPTTTreeIDManager

        new_id = MPTTTreeIDManager.objects.create().id
        return new_id

    @contextlib.contextmanager
    def lock_mptt(self, *tree_ids):
        # If this is not inside the context of a delay context manager
        # or updates are not disabled set a lock on the tree_ids.
        if not self.model._mptt_is_tracking and self.model._mptt_updates_enabled:
            with transaction.atomic():
                # Lock only MPTT columns for updates on any of the tree_ids specified
                # until the end of this transaction
                query = Q()
                for tree_id in tree_ids:
                    query |= Q(tree_id=tree_id)
                self.select_for_update().order_by().filter(query).values(
                    "tree_id", "lft", "rght"
                )
                yield
        else:
            # Otherwise just let it carry on!
            yield

    def partial_rebuild(self, tree_id):
        with self.lock_mptt(tree_id):
            return super(CustomContentNodeTreeManager, self).partial_rebuild(tree_id)

    def _move_child_to_new_tree(self, node, target, position):
        from contentcuration.models import PrerequisiteContentRelationship

        super(CustomContentNodeTreeManager, self)._move_child_to_new_tree(
            node, target, position
        )
        PrerequisiteContentRelationship.objects.filter(
            Q(prerequisite_id=node.id) | Q(target_node_id=node.id)
        ).delete()

    @contextlib.contextmanager
    def _update_changes(self, node, save):
        original_parent_id = node.parent_id
        yield
        ids = [original_parent_id, node.parent_id] + [node.id] if save else []
        # Always write to the database for the parent change updates, as we have
        # no persistent object references for the original and new parent to modify
        if ids:
            self.filter(id__in=ids).update(changed=True)
        node.changed = True

    def _move_node(
        self, node, target, position="last-child", save=True, refresh_target=True
    ):
        # If we are delaying updates, then _move_node defers to insert_node
        # we are already wrapping for parent changes below, so no need to
        # add our parent changes context manager.
        if self.tree_model._mptt_is_tracking:
            return super(CustomContentNodeTreeManager, self)._move_node(
                node, target, position, save, refresh_target
            )
        with self._update_changes(node, save):
            return super(CustomContentNodeTreeManager, self)._move_node(
                node, target, position, save, refresh_target
            )

    def insert_node(
        self,
        node,
        target,
        position="last-child",
        save=False,
        allow_existing_pk=False,
        refresh_target=True,
    ):
        with self._update_changes(node, save):
            if save:
                with self.lock_mptt(target.tree_id):
                    return super(CustomContentNodeTreeManager, self).insert_node(
                        node, target, position, save, allow_existing_pk, refresh_target
                    )
            return super(CustomContentNodeTreeManager, self).insert_node(
                node, target, position, save, allow_existing_pk, refresh_target
            )

    def move_node(self, node, target, position="first-child"):
        with self.lock_mptt(node.tree_id, target.tree_id):
            super(CustomContentNodeTreeManager, self).move_node(node, target, position)

    def build_tree_nodes(self, data, target=None, position="last-child"):
        """
        vendored from:
        https://github.com/django-mptt/django-mptt/blob/fe2b9cc8cfd8f4b764d294747dba2758147712eb/mptt/managers.py#L614
        """
        opts = self.model._mptt_meta
        if target:
            tree_id = target.tree_id
            if position in ("left", "right"):
                level = getattr(target, opts.level_attr)
                if position == "left":
                    cursor = getattr(target, opts.left_attr)
                else:
                    cursor = getattr(target, opts.right_attr) + 1
            else:
                level = getattr(target, opts.level_attr) + 1
                if position == "first-child":
                    cursor = getattr(target, opts.left_attr) + 1
                else:
                    cursor = getattr(target, opts.right_attr)
        else:
            tree_id = self._get_next_tree_id()
            cursor = 1
            level = 0

        stack = []

        def treeify(data, cursor=1, level=0):
            data = dict(data)
            children = data.pop("children", [])
            node = self.model(**data)
            stack.append(node)
            setattr(node, opts.tree_id_attr, tree_id)
            setattr(node, opts.level_attr, level)
            setattr(node, opts.left_attr, cursor)
            for child in children:
                cursor = treeify(child, cursor=cursor + 1, level=level + 1)
            cursor += 1
            setattr(node, opts.right_attr, cursor)
            return cursor

        treeify(data, cursor=cursor, level=level)

        if target:
            self._create_space(2 * len(stack), cursor - 1, tree_id)

        return stack
