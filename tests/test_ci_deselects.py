"""Every --deselect in CI names a test that exists.

WHY THIS EXISTS. A `--deselect` whose path matches nothing is SILENTLY
IGNORED by pytest. It does not warn and it does not fail; the run simply
collects everything and the exemption quietly stops applying. Two of these
have been added to this repository by hand, and a third would have been
just as easy to mistype.

That makes a deselect an exemption with no reason attached, which is the
failure shape this repository keeps recording elsewhere: a licence that
outlives its subject, or one that never had a subject at all. This test
reads the workflow, extracts every deselect argument, and asserts that
pytest can still collect the node it names.

WHAT IT DOES NOT DO. It does not judge whether the deselect is justified --
that is what KNOWN_ISSUES.md is for, and prose cannot be checked. It only
proves the exemption still points at something real.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'

#: A deselect USE, not the word. The argument must contain `::`, because
#: the comment block above the run lines says "and --deselect to skip
#: CI-incompatible tests" -- and a pattern that matches the token alone
#: reads that sentence as an exemption named `to`, then fails because no
#: test called `to` exists. This test failed exactly that way when it was
#: written, which is the eighth time use-versus-mention has caught a check
#: in this programme. Match the claim, never the token.
DESELECT = re.compile(r'--deselect\s+"?([^\s"]+::[^\s"]+)"?')


def _deselects() -> list[tuple[str, str]]:
    out = []
    for workflow in sorted(WORKFLOWS.glob('*.yml')):
        text = workflow.read_text(encoding='utf-8')
        for match in DESELECT.finditer(text):
            out.append((workflow.name, match.group(1)))
    return out


def test_the_workflows_are_where_this_test_thinks_they_are():
    """Guard the guard. If the directory moved, every assertion below would
    iterate an empty list and pass."""
    assert WORKFLOWS.is_dir(), f'no workflow directory at {WORKFLOWS}'
    assert list(WORKFLOWS.glob('*.yml')), 'no workflow files found'


def test_at_least_one_deselect_is_still_declared():
    """The sweep exists because deselects exist. If they are all gone, this
    file should be deleted rather than left passing over nothing."""
    found = _deselects()
    assert found, (
        'no --deselect found in any workflow. If CI no longer needs any, '
        'delete this test in the same commit that removed the last one.')


@pytest.mark.parametrize('workflow,node', _deselects(),
                         ids=lambda v: v.replace('/', '-'))
def test_every_deselected_node_still_exists(workflow: str, node: str):
    """pytest ignores a --deselect that matches nothing, so a typo or a
    renamed class turns the exemption off without saying so."""
    path = node.split('::', 1)[0]
    assert (ROOT / path).exists(), (
        f'{workflow} deselects {node}, but {path} does not exist')
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', node, '--collect-only', '-q',
         '-p', 'no:cacheprovider'],
        cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0 and 'no tests ran' not in result.stdout, (
        f'{workflow} deselects {node}, which pytest cannot collect.\n'
        f'A --deselect that matches nothing is silently ignored, so this '
        f'exemption is not doing anything.\n\n{result.stdout[-800:]}')


def test_the_documented_family_is_the_one_that_is_deselected():
    """KNOWN_ISSUES.md prescribes deselecting the AsyncFileOps family on
    Linux when it becomes noisy. This is the link between the prose and the
    workflow, asserted in the one direction that can be."""
    nodes = {node for _w, node in _deselects()}
    linux = [n for n in nodes if 'AsyncFileOps' in n]
    assert len(linux) >= 2, (
        f'expected both AsyncFileOps classes to be deselected on Linux, '
        f'found {sorted(linux)}')
    known = (ROOT / 'KNOWN_ISSUES.md').read_text(encoding='utf-8')
    for node in linux:
        cls = node.rsplit('::', 1)[-1]
        assert cls in known, (
            f'{cls} is deselected in CI but not described in '
            f'KNOWN_ISSUES.md. A deselect with no written reason is an '
            f'exemption nobody can review.')
