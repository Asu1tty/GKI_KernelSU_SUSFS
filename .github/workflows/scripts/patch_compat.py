"""Narrow adaptations for known upstream SUSFS patch context differences."""
import re


def adapt_namespace_context(patch: str, namespace_source: str) -> str:
    # The pinned 5.15/6.1 patches were generated with this unrelated include.
    # Most release branches lack it. Remove only the unchanged context line;
    # all SUSFS additions/deletions must remain intact.
    context = ' #include <trace/hooks/blk.h>\n'
    if '#include <trace/hooks/blk.h>' in namespace_source:
        return patch
    sections = re.split(r'(?=^diff --git )', patch, flags=re.MULTILINE)
    for i, section in enumerate(sections):
        if not section.startswith('diff --git a/fs/namespace.c b/fs/namespace.c\n'):
            continue
        hunks = re.split(r'(?=^@@ )', section, flags=re.MULTILINE)
        for j, hunk in enumerate(hunks):
            if context not in hunk:
                continue
            if hunk.count(context) != 1:
                raise ValueError('Unexpected repeated blk.h context in namespace patch')
            header, body = hunk.split('\n', 1)
            match = re.fullmatch(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@(.*)', header)
            if not match:
                raise ValueError(f'Unexpected namespace patch header: {header}')
            old_start, old_count, new_start, new_count, suffix = match.groups()
            header = (f'@@ -{old_start},{int(old_count) - 1} '
                      f'+{new_start},{int(new_count) - 1} @@{suffix}')
            hunks[j] = header + '\n' + body.replace(context, '', 1)
        sections[i] = ''.join(hunks)
    return ''.join(sections)
