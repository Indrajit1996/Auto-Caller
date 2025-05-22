import importlib
import pkgutil
from pathlib import Path

from sqlmodel import Session, select

from app.api.keystone.utils.user import get_password_hash
from app.models.user import User, UserStatus


def create_user(
    session: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    is_superuser: bool = False,
    status: UserStatus = UserStatus.ACTIVE,
) -> User | None:
    """
    Common function to create a user that can be reused across the application.
    """

    existing_user = session.exec(select(User).where(User.email == email)).first()

    if existing_user:
        return None

    # Create user object
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        is_superuser=is_superuser,
        status=status,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


def discover_data_pipeline_components() -> None:
    """
    Automatically discover and import all components to register them.
    Call this at application startup.
    """
    base_path = Path(__file__).parent.parent.parent / "data_pipeline"
    component_dirs = [
        base_path / "importers",
        base_path / "seeders",
        base_path / "scripts",
    ]

    # Also include the base directory for pipeline scripts
    component_dirs.append(base_path)

    for dir_path in component_dirs:
        if not dir_path.exists():
            continue

        # Get the package name from the directory path
        pkg_name = ".".join(dir_path.relative_to(base_path.parent.parent).parts)

        # Import all modules in the directory
        if dir_path == base_path:
            # For the base directory, only import specific pipeline scripts
            for script_name in ["process_data", "import_data", "seed_data"]:
                script_path = dir_path / f"{script_name}.py"
                if script_path.exists():
                    importlib.import_module(f"{pkg_name}.{script_name}")
        else:
            # For component directories, import all Python files
            for _, name, is_pkg in pkgutil.iter_modules([str(dir_path)]):
                if not is_pkg and not name.startswith("__"):
                    importlib.import_module(f"{pkg_name}.{name}")

    print("Component discovery complete")
