"""The checklist: the parts of the spec the conformance kit cannot decide, grouped by where their evidence lives."""

from functools import cache
from pathlib import Path

from pydantic import BaseModel, ValidationError
import yaml

from smart_tool_creator.schemas import ReviewGroup, SmartToolCreatorError, SpecCheck

# The checklist ships as Markdown rather than as Python constants so each check reads like what it is:
# its spec sentence in the frontmatter, quoted verbatim, and the reviewer's calibration below it.
CHECKS_ROOT = Path(__file__).parent / "checks"
GROUP_FILE = "GROUP.md"
CHECK_SUFFIX = ".md"


class GroupFrontmatter(BaseModel):
    """The frontmatter of a group's GROUP.md."""

    name: str
    order: int
    read_first: list[str]
    checks: list[str]


class CheckFrontmatter(BaseModel):
    """The frontmatter of one check's Markdown file; its id is the file's stem."""

    spec_file: str
    spec: str


@cache
def review_groups() -> list[ReviewGroup]:
    """The checklist as it ships: one directory per group under `checks/`, one Markdown file per check."""
    if not CHECKS_ROOT.is_dir():
        raise SmartToolCreatorError(
            f"The spec adherence checklist is missing: {CHECKS_ROOT} is not a directory. "
            "Reinstall the tool so the checklist ships with the package."
        )
    loaded = [_group(directory) for directory in sorted(path for path in CHECKS_ROOT.iterdir() if path.is_dir())]
    _one_order_each(loaded)
    groups = [group for _, group in sorted(loaded, key=lambda pair: pair[0])]
    _one_definition_each(groups)
    return groups


def checks_by_id() -> dict[str, SpecCheck]:
    """Every check of the checklist, keyed by id, in the checklist's order."""
    return {check.id: check for group in review_groups() for check in group.checks}


def select(ids: list[str] | None) -> list[ReviewGroup]:
    """The groups pruned to `ids`, dropping a group none of them falls in; every group when `ids` is None."""
    if ids is None:
        return list(review_groups())
    known = checks_by_id()
    if not ids:
        raise SmartToolCreatorError(
            f"No checks were selected. Pass None to review every check, or at least one of: {', '.join(known)}."
        )
    unknown = [identifier for identifier in ids if identifier not in known]
    if unknown:
        raise SmartToolCreatorError(
            f"Not a check of the spec adherence checklist: {', '.join(unknown)}. The checks are: {', '.join(known)}."
        )
    wanted = set(ids)
    groups = []
    for group in review_groups():
        checks = [check for check in group.checks if check.id in wanted]
        if checks:
            groups.append(
                ReviewGroup(name=group.name, read_first=group.read_first, guidance=group.guidance, checks=checks)
            )
    return groups


def _group(directory: Path) -> tuple[int, ReviewGroup]:
    """One group: its GROUP.md, then the checks it lists, in the order it lists them."""
    group_path = directory / GROUP_FILE
    if not group_path.is_file():
        raise SmartToolCreatorError(
            f"The checklist group at {directory} has no {GROUP_FILE}. "
            f"Add one declaring the group's name, order, read_first, and checks, or delete {directory}."
        )
    frontmatter, guidance = _document(group_path)
    try:
        header = GroupFrontmatter.model_validate(frontmatter)
    except ValidationError as error:
        raise SmartToolCreatorError(
            f"The frontmatter of {group_path} is not a checklist group: {error}. "
            "It needs a name, an order, a read_first list, and a checks list."
        ) from None
    present = {path.stem: path for path in sorted(directory.glob(f"*{CHECK_SUFFIX}")) if path.name != GROUP_FILE}
    missing = [identifier for identifier in header.checks if identifier not in present]
    if missing:
        raise SmartToolCreatorError(
            f"{group_path} lists checks that have no file: {', '.join(missing)}. "
            f"Write {directory}/<id>{CHECK_SUFFIX} for each, or drop it from the group's checks."
        )
    stray = [path.name for identifier, path in present.items() if identifier not in header.checks]
    if stray:
        raise SmartToolCreatorError(
            f"The checklist group at {directory} holds check files its {GROUP_FILE} does not list: "
            f"{', '.join(stray)}. Add each to the group's checks, or delete the file."
        )
    checks = [_check(present[identifier]) for identifier in header.checks]
    return header.order, ReviewGroup(name=header.name, read_first=header.read_first, guidance=guidance, checks=checks)


def _check(path: Path) -> SpecCheck:
    """One check: its spec sentence from the frontmatter, the reviewer's guidance from the body."""
    frontmatter, guidance = _document(path)
    try:
        header = CheckFrontmatter.model_validate(frontmatter)
    except ValidationError as error:
        raise SmartToolCreatorError(
            f"The frontmatter of {path} is not a checklist check: {error}. "
            "It needs a spec_file and the spec sentence the check operationalizes."
        ) from None
    if not guidance:
        raise SmartToolCreatorError(
            f"The check at {path} carries no guidance below its frontmatter. "
            "Write what the reviewer decides, what adheres, what deviates, and where to look, or delete the file."
        )
    return SpecCheck(id=path.stem, spec_file=header.spec_file, spec=header.spec, guidance=guidance)


def _document(path: Path) -> tuple[dict[str, object], str]:
    """A checklist file's frontmatter and body, read the way the manifest's are."""
    parts = path.read_text(encoding="utf-8").split("---", 2)
    if len(parts) != 3:
        raise SmartToolCreatorError(
            f"{path} has no YAML frontmatter. Open the file with a '---' line, close it with another, "
            "and write the Markdown below that."
        )
    frontmatter = yaml.safe_load(parts[1])
    if not isinstance(frontmatter, dict):
        raise SmartToolCreatorError(
            f"The frontmatter of {path} is not a YAML mapping. Write it as `key: value` lines between the "
            "'---' markers."
        )
    return frontmatter, parts[2].strip()


def _one_order_each(loaded: list[tuple[int, ReviewGroup]]) -> None:
    """Two groups claiming one order would leave the checklist's order up to the filesystem."""
    seen: dict[int, str] = {}
    for order, group in loaded:
        if order in seen:
            raise SmartToolCreatorError(
                f"The checklist groups '{seen[order]}' and '{group.name}' both declare order {order}. "
                f"Give each group an order of its own in its {GROUP_FILE}."
            )
        seen[order] = group.name


def _one_definition_each(groups: list[ReviewGroup]) -> None:
    """An id in two groups would make a selection ambiguous and a finding unattributable."""
    seen: dict[str, str] = {}
    for group in groups:
        for check in group.checks:
            if check.id in seen:
                raise SmartToolCreatorError(
                    f"The check '{check.id}' is defined in both the '{seen[check.id]}' and '{group.name}' groups. "
                    "Rename one of the two files so every check id is unique."
                )
            seen[check.id] = group.name
