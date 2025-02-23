const loadVersions = async () => {
  const res = await fetch(
    DOCUMENTATION_OPTIONS.URL_ROOT + "_static/versions.json",
  );
  if (res.status !== 200) {
    return null;
  }
  return await res.json();
};

const addVersionWarning = (currentVersion, latestVersion) => {
  if (currentVersion === latestVersion) {
    return;
  }

  const header = document.querySelector(".bd-header__inner")?.parentElement;
  if (!header) {
    return;
  }

  const container = document.createElement("div");
  container.id = "version-warning";

  const isPreviewVersion = (version) => {
        const previewVersions = ['dev', 'develop', 'main', '3-dev'];
        return previewVersions.includes(version) || parseInt(version) > parseInt(latestVersion);
    };

    const warningText = document.createElement("span");
    warningText.textContent = `You are viewing the documentation for ${
        isPreviewVersion(currentVersion) ? "a preview" : "an outdated"
    } version of Litestar.`;
  container.appendChild(warningText);

  const latestLink = document.createElement("a");
  latestLink.textContent = "Click here to go to the latest version";
  latestLink.href = DOCUMENTATION_OPTIONS.URL_ROOT + "../latest";
  container.appendChild(latestLink);

  header.before(container);
};

const formatVersionName = (version, isLatest) =>
  version + (isLatest ? " (latest)" : "");

const addVersionSelect = (currentVersion, versionSpec) => {
  const navEnd = document.querySelector(".navbar-header-items__end");

  if (!navEnd) {
    return;
  }

  const container = document.createElement("div");
  container.classList.add("navbar-nav");

  const dropdown = document.createElement("div");
  dropdown.classList.add("dropdown");
  container.appendChild(dropdown);

  const dropdownToggle = document.createElement("button");
  dropdownToggle.classList.add("btn", "dropdown-toggle", "nav-item");
  dropdownToggle.setAttribute("data-bs-toggle", "dropdown");
  dropdownToggle.setAttribute("type", "button");
  dropdownToggle.textContent = `Version: ${formatVersionName(
    currentVersion,
    currentVersion === versionSpec.latest,
  )}`;
  dropdown.appendChild(dropdownToggle);

  const dropdownContent = document.createElement("div");
  dropdownContent.classList.add("dropdown-menu");
  dropdown.appendChild(dropdownContent);

  for (const version of versionSpec.versions) {
    const navItem = document.createElement("li");
    navItem.classList.add("nav-item");

    const navLink = document.createElement("a");
    navLink.classList.add("nav-link", "nav-internal");
    navLink.href = DOCUMENTATION_OPTIONS.URL_ROOT + `../${version}`;
    navLink.textContent = formatVersionName(
      version,
      version === versionSpec.latest,
    );
    navItem.appendChild(navLink);

    dropdownContent.appendChild(navItem);
  }

  navEnd.prepend(container);
};

const setupVersioning = (versions) => {
  if (versions === null) {
    return;
  }

  const currentVersion = DOCUMENTATION_OPTIONS.VERSION;

  addVersionWarning(currentVersion, versions.latest);
  addVersionSelect(currentVersion, versions);
};

window.addEventListener("DOMContentLoaded", () => {
  loadVersions().then(setupVersioning);
});
