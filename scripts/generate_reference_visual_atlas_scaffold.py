#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from string import Template
from typing import Iterable

from repo_root_resolution_common import resolve_repo_root

TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates" / "reference_visual_atlas"
ATLAS_DOC_TEMPLATE = TEMPLATE_ROOT / "atlas_doc.template.md"
VALIDATOR_TEMPLATE = TEMPLATE_ROOT / "validator.template.py"
NEXT_STEPS_TEMPLATE = TEMPLATE_ROOT / "next_steps.template.md"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALIDATOR_SLUG_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?$")
STATUS_KEY_RE = re.compile(r"^[a-z0-9_]+_status$")
ERROR_CODE_RE = re.compile(r"^[A-Z0-9-]+$")
SVG_RE = re.compile(r"^(?P<stem>[a-z0-9_]+)_v(?P<version>[0-9A-Za-z.]+)\.svg$")
OWNER_DOC_RE = re.compile(r"^docs/(?:governance|review)/[A-Za-z0-9._/\-]+\.md$")


@dataclass(frozen=True)
class ScaffoldSpec:
    atlas_family_slug: str
    doc_version: str
    stream_version: str
    validator_slug: str
    title: str
    surface_summary: str
    purpose_sentence: str
    status_key: str
    error_code: str
    owner_docs: tuple[str, ...]
    svg_names: tuple[str, ...]
    output_root: str

    @property
    def canonical_doc_rel(self) -> str:
        return f"docs/references/{self.atlas_family_slug}-{self.doc_version}.md"

    @property
    def canonical_asset_root_rel(self) -> str:
        return f"docs/references/assets/{self.atlas_family_slug}"

    @property
    def validator_script_rel(self) -> str:
        return f"scripts/validate_{self.validator_slug}_visual_atlas_governance.py"

    @property
    def asset_topic_label(self) -> str:
        token = self.atlas_family_slug
        for prefix in ("identity-protocol-", "identity-", "protocol-"):
            if token.startswith(prefix):
                token = token[len(prefix) :]
                break
        for suffix in ("-visual-atlas", "-atlas"):
            if token.endswith(suffix):
                token = token[: -len(suffix)]
                break
        return token.replace("-", " ").strip() or self.atlas_family_slug.replace("-", " ")

    @property
    def status_line(self) -> str:
        return f"Status: Active canonical visual reference for the frozen {self.surface_summary}."

    @property
    def svg_family_pattern(self) -> str:
        stems = sorted({_svg_stem(name) for name in self.svg_names})
        if not stems:
            return r"^$"
        union = "|".join(re.escape(stem) for stem in stems)
        return rf"^({union})_v[0-9A-Za-z.]+\.svg$"

    @property
    def atlas_doc_pattern(self) -> str:
        return rf"^{re.escape(self.atlas_family_slug)}-v[0-9.]+\.md$"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _svg_stem(name: str) -> str:
    match = SVG_RE.fullmatch(name)
    if not match:
        raise ValueError(f"invalid svg name: {name}")
    return match.group("stem")


def _unique_preserve(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in items:
        token = str(raw or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return tuple(out)


def _build_spec(args: argparse.Namespace) -> ScaffoldSpec:
    atlas_family_slug = str(args.atlas_family_slug or "").strip()
    validator_slug = str(args.validator_slug or "").strip()
    doc_version = str(args.doc_version or "").strip()
    stream_version = str(args.stream_version or "").strip()
    title = str(args.title or "").strip()
    surface_summary = str(args.surface_summary or "").strip().rstrip(". ")
    purpose_sentence = str(args.purpose_sentence or "").strip().rstrip(". ")
    status_key = str(args.status_key or "").strip()
    error_code = str(args.error_code or "").strip()
    owner_docs = _unique_preserve(args.owner_doc or [])
    svg_names = _unique_preserve(args.svg_name or [])
    output_root = str(args.output_root or "").strip()

    _require(SLUG_RE.fullmatch(atlas_family_slug) is not None, "atlas-family-slug must be lowercase kebab-case")
    _require(VALIDATOR_SLUG_RE.fullmatch(validator_slug) is not None, "validator-slug must be lowercase snake_case")
    _require(VERSION_RE.fullmatch(doc_version) is not None, "doc-version must look like v1.6 or v1.6.18")
    _require(VERSION_RE.fullmatch(stream_version) is not None, "stream-version must look like v1.6 or v1.6.18")
    _require(bool(title), "title is required")
    _require(bool(surface_summary), "surface-summary is required")
    _require(bool(purpose_sentence), "purpose-sentence is required")
    _require(STATUS_KEY_RE.fullmatch(status_key) is not None, "status-key must be lowercase snake_case ending with _status")
    _require(ERROR_CODE_RE.fullmatch(error_code) is not None, "error-code must be uppercase letters/numbers/hyphens")
    _require(bool(output_root), "output-root is required")
    _require(bool(owner_docs), "at least one --owner-doc is required")
    _require(bool(svg_names), "at least one --svg-name is required")
    for owner_doc in owner_docs:
        _require(
            OWNER_DOC_RE.fullmatch(owner_doc) is not None,
            f"owner-doc must stay under docs/governance or docs/review: {owner_doc}",
        )
    for svg_name in svg_names:
        _require(
            SVG_RE.fullmatch(svg_name) is not None,
            f"svg-name must be version-stamped like example_surface_v1618.svg: {svg_name}",
        )

    return ScaffoldSpec(
        atlas_family_slug=atlas_family_slug,
        doc_version=doc_version,
        stream_version=stream_version,
        validator_slug=validator_slug,
        title=title,
        surface_summary=surface_summary,
        purpose_sentence=purpose_sentence,
        status_key=status_key,
        error_code=error_code,
        owner_docs=owner_docs,
        svg_names=svg_names,
        output_root=output_root,
    )


def _load_template(path: Path) -> Template:
    return Template(path.read_text(encoding="utf-8"))


def _format_svg_inventory(spec: ScaffoldSpec) -> str:
    lines: list[str] = []
    for idx, svg_name in enumerate(spec.svg_names, start=1):
        rel_link = f"assets/{spec.atlas_family_slug}/{svg_name}"
        lines.extend(
            [
                f"{idx}. Path: `{spec.canonical_asset_root_rel}/{svg_name}`",
                f"   - Relative link: [{svg_name}]({rel_link})",
            ]
        )
    return "\n".join(lines)


def _format_python_tuple(items: Iterable[str], indent: int = 4) -> str:
    prefix = " " * indent
    return "\n".join(f'{prefix}"{item}",' for item in items)


def _format_owner_doc_bullets(items: Iterable[str], indent: int = 3) -> str:
    prefix = " " * indent
    return "\n".join(f"{prefix}- `{item}`" for item in items)


def _format_owner_doc_markers(spec: ScaffoldSpec, indent: int = 8) -> str:
    prefix = " " * indent
    tuple_indent = indent + 4
    rows: list[str] = []
    for owner_doc in spec.owner_docs:
        rows.append(f'{prefix}"{owner_doc}": (')
        rows.extend(
            [
                f'{ " " * tuple_indent}"{spec.canonical_doc_rel}",',
                f'{ " " * tuple_indent}"{spec.canonical_asset_root_rel}/",',
                f'{ " " * tuple_indent}"The canonical explanatory visual atlas for this stream is:",',
            ]
        )
        rows.append(f"{prefix}),")
    return "\n".join(rows)


def _render_templates(spec: ScaffoldSpec, repo_root: Path, output_root: Path) -> dict[str, str]:
    atlas_doc = _load_template(ATLAS_DOC_TEMPLATE)
    validator = _load_template(VALIDATOR_TEMPLATE)
    next_steps = _load_template(NEXT_STEPS_TEMPLATE)

    atlas_required_markers = (
        spec.status_line,
        "Classification: protocol-owned explanatory atlas; not a normative contract source.",
        "Canonical atlas markdown path is fixed to:",
        f"Canonical asset root for all protocol-owned {spec.asset_topic_label} visuals is fixed to:",
        "do not scatter them across `docs/governance/`, `docs/review/`, `activity/evidence/`, or ad-hoc workspace folders",
        "The anti-scatter guarantee frozen by this atlas is limited to the `identity-protocol-local` repository surface.",
        f"This atlas explains {spec.purpose_sentence} only.",
        "No diagram in this atlas may introduce backward compatibility, backstop, downgrade, lagging-pack shortcut, or undeclared rescue semantics.",
    )

    substitutions = {
        "atlas_title": spec.title,
        "status_line": spec.status_line,
        "stream_version": spec.stream_version,
        "surface_summary": spec.surface_summary,
        "purpose_sentence": spec.purpose_sentence,
        "canonical_doc_rel": spec.canonical_doc_rel,
        "canonical_asset_root_rel": spec.canonical_asset_root_rel,
        "canonical_asset_root_rel_slash": f"{spec.canonical_asset_root_rel}/",
        "validator_script_rel": spec.validator_script_rel,
        "asset_topic_label": spec.asset_topic_label,
        "svg_inventory_block": _format_svg_inventory(spec),
        "required_svg_files_py": _format_python_tuple(spec.svg_names, indent=8),
        "atlas_required_markers_py": _format_python_tuple(atlas_required_markers, indent=8),
        "index_required_markers_py": _format_python_tuple(
            (
                f"`{spec.canonical_doc_rel}`",
                f"asset root: `{spec.canonical_asset_root_rel}/`",
            ),
            indent=8,
        ),
        "owner_doc_markers_py": _format_owner_doc_markers(spec, indent=8),
        "status_key": spec.status_key,
        "error_code": spec.error_code,
        "svg_family_pattern": spec.svg_family_pattern,
        "atlas_doc_pattern": spec.atlas_doc_pattern,
        "manifest_json": json.dumps(
            {
                **asdict(spec),
                "repo_root": str(repo_root),
                "template_root": str(TEMPLATE_ROOT),
                "canonical_doc_rel": spec.canonical_doc_rel,
                "canonical_asset_root_rel": spec.canonical_asset_root_rel,
                "validator_script_rel": spec.validator_script_rel,
                "generated_preview_root": str(output_root),
                "generated_files": [
                    spec.canonical_doc_rel,
                    spec.validator_script_rel,
                    f"{spec.canonical_asset_root_rel}/.gitkeep",
                    "NEXT_STEPS.md",
                    "reference_visual_atlas_scaffold_manifest.json",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "owner_docs_bullets": _format_owner_doc_bullets(spec.owner_docs, indent=3),
    }

    return {
        spec.canonical_doc_rel: atlas_doc.substitute(substitutions).rstrip() + "\n",
        spec.validator_script_rel: validator.substitute(substitutions).rstrip() + "\n",
        "NEXT_STEPS.md": next_steps.substitute(substitutions).rstrip() + "\n",
        "reference_visual_atlas_scaffold_manifest.json": substitutions["manifest_json"] + "\n",
        f"{spec.canonical_asset_root_rel}/.gitkeep": "",
    }


def _write_files(output_root: Path, rendered: dict[str, str], *, force: bool) -> None:
    for rel_path, content in rendered.items():
        target = output_root / rel_path
        if target.exists() and not force:
            raise FileExistsError(f"refusing to overwrite existing path without --force: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _emit_manifest(
    spec: ScaffoldSpec,
    repo_root: Path,
    output_root: Path,
    rendered: dict[str, str],
    *,
    write_mode: str,
) -> str:
    payload = {
        "reference_visual_atlas_scaffold_status": "PASS_PREVIEW" if write_mode == "dry_run" else "PASS_WRITTEN",
        "write_mode": write_mode,
        "repo_root": str(repo_root),
        "template_root": str(TEMPLATE_ROOT),
        "output_root": str(output_root),
        "canonical_doc": spec.canonical_doc_rel,
        "canonical_asset_root": spec.canonical_asset_root_rel,
        "validator_script": spec.validator_script_rel,
        "owner_docs": list(spec.owner_docs),
        "required_svg_files": list(spec.svg_names),
        "generated_paths": sorted(rendered),
        "non_canonical_output_notice": (
            "Scaffold output is preview-only until copied into the protocol repo, registered in stream-doc-registry, "
            "backlinked from owner docs, indexed in AUDIT_SNAPSHOT_INDEX, and validated by the thin atlas validator."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a standardized preview scaffold for a future protocol-owned visual atlas family "
            "using the shared docs/references + validator onboarding contract."
        )
    )
    parser.add_argument("--repo-root", default="", help="Optional protocol repo root override.")
    parser.add_argument("--output-root", required=True, help="Preview root where the scaffold tree will be written.")
    parser.add_argument("--atlas-family-slug", required=True, help="Kebab-case atlas family slug, without version suffix.")
    parser.add_argument("--doc-version", required=True, help="Atlas markdown version suffix such as v1.6.")
    parser.add_argument("--stream-version", required=True, help="Owning stream version such as v1.6.18.")
    parser.add_argument("--validator-slug", required=True, help="Snake_case slug used for validate_<slug>_visual_atlas_governance.py.")
    parser.add_argument("--title", required=True, help="Atlas markdown H1 title.")
    parser.add_argument(
        "--surface-summary",
        required=True,
        help="Short phrase completing 'frozen <surface-summary>' in the standard status line.",
    )
    parser.add_argument(
        "--purpose-sentence",
        required=True,
        help="Short sentence fragment describing what the atlas visualizes; reused by markdown + validator markers.",
    )
    parser.add_argument("--status-key", required=True, help="JSON status key for the thin atlas validator.")
    parser.add_argument("--error-code", required=True, help="Error code emitted when the atlas governance validator fails.")
    parser.add_argument(
        "--svg-name",
        action="append",
        default=[],
        help="Version-stamped SVG filename to reserve under the canonical asset root. Repeat for multiple SVGs.",
    )
    parser.add_argument(
        "--owner-doc",
        action="append",
        default=[],
        help="Owning governance/review doc path that must backlink the atlas. Repeat for multiple owner docs.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Render and report the scaffold manifest without writing files.")
    parser.add_argument("--json-only", action="store_true", help="Emit scaffold manifest JSON only.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output-root preview tree.")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        spec = _build_spec(args)
        repo_root = resolve_repo_root(args.repo_root, start=__file__)
        output_root = Path(spec.output_root).expanduser().resolve()
        rendered = _render_templates(spec, repo_root, output_root)
        if not args.dry_run:
            _write_files(output_root, rendered, force=bool(args.force))
        manifest = _emit_manifest(
            spec,
            repo_root,
            output_root,
            rendered,
            write_mode="dry_run" if args.dry_run else "write",
        )
    except Exception as exc:
        if args.json_only:
            print(
                json.dumps(
                    {
                        "reference_visual_atlas_scaffold_status": "FAIL_REQUIRED",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                    ensure_ascii=False,
                )
            )
            return 1
        print(f"[FAIL] reference visual atlas scaffold generation failed: {type(exc).__name__}: {exc}")
        return 1

    if args.json_only:
        print(manifest)
    else:
        payload = json.loads(manifest)
        print(f"[PASS] reference visual atlas scaffold {payload['write_mode']}: {payload['output_root']}")
        print(f" - atlas doc: {payload['canonical_doc']}")
        print(f" - validator: {payload['validator_script']}")
        print(f" - owner docs: {', '.join(payload['owner_docs'])}")
        print(f" - svg inventory: {', '.join(payload['required_svg_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
