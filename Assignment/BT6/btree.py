"""B-Tree (order 3) implementation for indexing."""

from collections import deque


class BTreeNode:
    def __init__(self, leaf=True):
        self.keys = []  # list[tuple[key, value]]
        self.children = []
        self.leaf = leaf


class BTree:
    def __init__(self, order=3):
        if order != 3:
            raise ValueError("This implementation is tailored for order=3 (2-3 tree)")
        self.order = order
        self.max_keys = order - 1
        self.root = BTreeNode(leaf=True)

    def insert(self, key, value):
        # Upsert semantics: if key exists, update value in-place in O(log n).
        found_node, found_idx = self._find_entry(self.root, key)
        if found_node is not None:
            found_node.keys[found_idx] = (key, value)
            return

        entry = (key, value)
        split_info = self._insert_recursive(self.root, entry)
        if split_info is not None:
            promoted, left, right = split_info
            new_root = BTreeNode(leaf=False)
            new_root.keys = [promoted]
            new_root.children = [left, right]
            self.root = new_root

    def _insert_recursive(self, node, entry):
        if node.leaf:
            self._insert_sorted(node.keys, entry)
            if len(node.keys) > self.max_keys:
                return self._split_node(node)
            return None

        idx = self._find_child_index(node.keys, entry[0])
        split_info = self._insert_recursive(node.children[idx], entry)
        if split_info is not None:
            promoted, left, right = split_info
            node.keys.insert(idx, promoted)
            node.children[idx] = left
            node.children.insert(idx + 1, right)

        if len(node.keys) > self.max_keys:
            return self._split_node(node)
        return None

    def _split_node(self, node):
        mid = len(node.keys) // 2
        promoted = node.keys[mid]

        left = BTreeNode(leaf=node.leaf)
        right = BTreeNode(leaf=node.leaf)

        left.keys = node.keys[:mid]
        right.keys = node.keys[mid + 1:]

        if not node.leaf:
            left.children = node.children[: mid + 1]
            right.children = node.children[mid + 1 :]

        return promoted, left, right

    def _insert_sorted(self, arr, entry):
        key = entry[0]
        idx = 0
        while idx < len(arr) and arr[idx][0] < key:
            idx += 1
        arr.insert(idx, entry)

    def _find_child_index(self, keys, key):
        idx = 0
        while idx < len(keys) and key > keys[idx][0]:
            idx += 1
        return idx

    def search(self, key):
        return self._search_recursive(self.root, key)

    def _find_entry(self, node, key):
        idx = 0
        while idx < len(node.keys) and key > node.keys[idx][0]:
            idx += 1

        if idx < len(node.keys) and key == node.keys[idx][0]:
            return node, idx

        if node.leaf:
            return None, None

        return self._find_entry(node.children[idx], key)

    def _search_recursive(self, node, key):
        idx = 0
        while idx < len(node.keys) and key > node.keys[idx][0]:
            idx += 1

        if idx < len(node.keys) and key == node.keys[idx][0]:
            return node.keys[idx][1]

        if node.leaf:
            return None

        return self._search_recursive(node.children[idx], key)

    def delete(self, key):
        removed = self._delete_recursive(self.root, key)

        if not removed:
            return False

        # Collapse empty root level when possible.
        if not self.root.leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

        # Keep at least an empty leaf root.
        if self.root is None:
            self.root = BTreeNode(leaf=True)
        return True

    def _delete_recursive(self, node, key):
        idx = 0
        while idx < len(node.keys) and key > node.keys[idx][0]:
            idx += 1

        if node.leaf:
            if idx < len(node.keys) and node.keys[idx][0] == key:
                node.keys.pop(idx)
                return True
            return False

        # Key exists in internal node: replace by predecessor from left subtree.
        if idx < len(node.keys) and node.keys[idx][0] == key:
            pred = self._max_entry(node.children[idx])
            node.keys[idx] = pred
            deleted = self._delete_recursive(node.children[idx], pred[0])
            if len(node.children[idx].keys) == 0:
                self._rebalance_child(node, idx)
            return deleted

        # Key not in this node: recurse into corresponding child.
        child_idx = idx
        deleted = self._delete_recursive(node.children[child_idx], key)
        if len(node.children[child_idx].keys) == 0:
            self._rebalance_child(node, child_idx)
        return deleted

    def _max_entry(self, node):
        cur = node
        while not cur.leaf:
            cur = cur.children[-1]
        return cur.keys[-1]

    def _rebalance_child(self, parent, child_idx):
        child = parent.children[child_idx]
        if len(child.keys) > 0:
            return

        left_idx = child_idx - 1
        right_idx = child_idx + 1
        left = parent.children[left_idx] if left_idx >= 0 else None
        right = parent.children[right_idx] if right_idx < len(parent.children) else None

        # Borrow from left sibling when it has spare key.
        if left is not None and len(left.keys) > 1:
            child.keys.insert(0, parent.keys[left_idx])
            parent.keys[left_idx] = left.keys.pop()
            if not left.leaf:
                child.children.insert(0, left.children.pop())
                child.leaf = False
            return

        # Borrow from right sibling when it has spare key.
        if right is not None and len(right.keys) > 1:
            child.keys.append(parent.keys[child_idx])
            parent.keys[child_idx] = right.keys.pop(0)
            if not right.leaf:
                child.children.append(right.children.pop(0))
                child.leaf = False
            return

        # Merge with a sibling (both siblings are minimal) plus separator key from parent.
        if left is not None:
            left.keys.append(parent.keys.pop(left_idx))
            left.keys.extend(child.keys)
            if not child.leaf:
                left.children.extend(child.children)
                left.leaf = False
            parent.children.pop(child_idx)
            return

        if right is not None:
            child.keys.append(parent.keys.pop(child_idx))
            child.keys.extend(right.keys)
            if not right.leaf:
                child.children.extend(right.children)
                child.leaf = False
            parent.children.pop(right_idx)

    def get_all_entries(self):
        entries = []
        self._inorder(self.root, entries)
        return entries

    def _inorder(self, node, out):
        if node.leaf:
            out.extend(node.keys)
            return

        for i, entry in enumerate(node.keys):
            self._inorder(node.children[i], out)
            out.append(entry)
        self._inorder(node.children[-1], out)

    def get_level_keys(self):
        levels = []
        queue = deque([(self.root, 0)])

        while queue:
            node, level = queue.popleft()
            if level >= len(levels):
                levels.append([])
            levels[level].append([entry[0] for entry in node.keys])

            if not node.leaf:
                for child in node.children:
                    queue.append((child, level + 1))

        return levels

    def export_tree(self):
        """Export full tree structure for UI visualization."""
        return self._export_node(self.root)

    def _export_node(self, node):
        return {
            "keys": [self._key_to_label(entry[0]) for entry in node.keys],
            "leaf": node.leaf,
            "children": [] if node.leaf else [self._export_node(child) for child in node.children],
        }

    def _key_to_label(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            return f"{key[0]} | {key[1]}"
        return str(key)

    def validate(self):
        leaf_depths = []
        ok, msg = self._validate_node(self.root, None, None, 0, leaf_depths, is_root=True)
        if not ok:
            return False, msg

        if len(set(leaf_depths)) > 1:
            return False, "leaves are not at the same depth"

        entries = self.get_all_entries()
        for i in range(1, len(entries)):
            if entries[i - 1][0] > entries[i][0]:
                return False, "in-order traversal is not sorted"

        # No duplicated keys should appear in canonical index tree.
        seen = set()
        for entry in entries:
            k = entry[0]
            if k in seen:
                return False, "duplicate key detected"
            seen.add(k)

        return True, "valid"

    def strict_check(self):
        """Return rich integrity info for diagnostics and tests."""
        ok, message = self.validate()
        entries = self.get_all_entries()
        return {
            "ok": ok,
            "message": message,
            "entry_count": len(entries),
            "levels": self.get_level_keys(),
        }

    def _validate_node(self, node, low, high, depth, leaf_depths, is_root=False):
        key_count = len(node.keys)

        if is_root:
            if key_count > self.max_keys:
                return False, "root has too many keys"
        else:
            if key_count < 1 or key_count > self.max_keys:
                return False, "non-root node violates key count constraints"

        for i in range(1, key_count):
            if node.keys[i - 1][0] > node.keys[i][0]:
                return False, "node keys are not sorted"

        for entry in node.keys:
            k = entry[0]
            if low is not None and k <= low:
                return False, "key violates lower bound"
            if high is not None and k >= high:
                return False, "key violates upper bound"

        if node.leaf:
            if node.children:
                return False, "leaf node has children"
            leaf_depths.append(depth)
            return True, "ok"

        if len(node.children) != key_count + 1:
            return False, "internal node children count mismatch"

        for i, child in enumerate(node.children):
            child_low = low if i == 0 else node.keys[i - 1][0]
            child_high = high if i == key_count else node.keys[i][0]
            ok, msg = self._validate_node(child, child_low, child_high, depth + 1, leaf_depths, is_root=False)
            if not ok:
                return ok, msg

        return True, "ok"
