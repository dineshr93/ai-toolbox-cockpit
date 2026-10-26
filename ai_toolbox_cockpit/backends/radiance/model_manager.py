"""Pinned standalone Radiance containers, with bundled vision and drafting tensors."""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

from ai_toolbox_cockpit.catalog import load_model_catalog
from ai_toolbox_cockpit.settings import get_backend_settings, save_backend_settings


@dataclass(frozen=True)
class RadianceModel:
    id: str
    name: str
    repo: str
    revision: str
    directory: str
    filename: str
    size_bytes: int
    family: str
    speculation: str
    draft_tokens: int
    context_size: int
    tensor_parallel: int
    vision: bool
    ngram_placement: str = 'auto'
    max_sessions: int = 1

    @classmethod
    def from_entry(cls, entry: dict) -> 'RadianceModel':
        model = cls(**{key: entry[key] for key in cls.__dataclass_fields__ if key in entry})
        if not re.fullmatch(r'[0-9a-f]{40}', model.revision):
            raise ValueError('Radiance models require an immutable repository revision.')
        for path in (model.directory, model.filename):
            if not path or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or '\\' in path or path.startswith('-'):
                raise ValueError('Radiance model paths must be safe relative paths.')
        if not model.filename.endswith('.rad') or len(PurePosixPath(model.filename).parts) != 1:
            raise ValueError('Select a compatible single-file .rad model container.')
        if type(model.size_bytes) is not int or model.size_bytes <= 0:
            raise ValueError('Radiance models require an exact positive file size.')
        if model.speculation not in {'mtp', 'dflash2'} or type(model.draft_tokens) is not int or not 1 <= model.draft_tokens <= 16:
            raise ValueError('Invalid bundled Radiance draft profile.')
        if isinstance(model.tensor_parallel, bool) or model.tensor_parallel not in {1, 2, 4}:
            raise ValueError('Invalid qualified Radiance GPU layout.')
        if model.ngram_placement not in {'auto', 'ram'}:
            raise ValueError('Invalid qualified n-gram placement.')
        if type(model.max_sessions) is not int or not 1 <= model.max_sessions <= 16:
            raise ValueError('Invalid qualified Radiance concurrency limit.')
        if type(model.context_size) is not int or not 1 <= model.context_size <= 262144:
            raise ValueError('Invalid Radiance context bound.')
        return model


def get_models_dir() -> Path:
    default = load_model_catalog().backends['radiance'].storage['default']
    return Path(get_backend_settings('radiance').get('models_dir', default)).expanduser().resolve()


def save_models_dir(value: str) -> bool:
    if not value.strip():
        return False
    try:
        path = Path(value).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError):
        return False
    return save_backend_settings('radiance', {'models_dir': str(path)})


def load_models() -> tuple[RadianceModel, ...]:
    return tuple(RadianceModel.from_entry(entry) for entry in load_model_catalog().backends['radiance'].entries)


def get_model(model_id: str) -> RadianceModel:
    for model in load_models():
        if model.id == model_id:
            return model
    raise ValueError('Select a curated standalone Radiance model.')


def resolved_path(model: RadianceModel, directory: Path | None = None) -> Path | None:
    root = directory if directory is not None else get_models_dir()
    for candidate in (root / model.directory / model.filename, root / model.filename):
        try:
            if candidate.is_file() and candidate.stat().st_size == model.size_bytes:
                return candidate.resolve()
        except OSError:
            continue
    return None


def model_status(model: RadianceModel, directory: Path | None = None) -> str:
    return 'Ready' if resolved_path(model, directory) else 'Missing / incomplete'


def download_command(model: RadianceModel, directory: Path) -> list[str]:
    sibling = Path(sys.executable).with_name('hf')
    hf = str(sibling) if sibling.is_file() else (shutil.which('hf') or 'hf')
    return [hf, 'download', model.repo, model.filename, '--revision', model.revision,
            '--local-dir', str(directory.expanduser().resolve() / model.directory)]
