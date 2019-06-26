# Development

Follow these steps to run the addon directly from source so that your changes will be reflected in Blender.

1. Clone the repository: `git clone git@github.com:AnalyticalGraphicsInc/cesium-ion-blender-addon.git`

1. Start Blender and uninstall any existing versions of the addon via `Edit->Preferences->Add-ons`. Exit blender.

1. Create a symbolic link to the `cesium-ion-blender-addon/io-cesium-ion` directory from your platform specific addon directory:

    - **Windows** `<Blender Install Location>\blender\[version]\addons\`
    - **Linux** `<Blender Install Location>/blender/[version]/addons/`
    - **macOS** `Users/[USER]/Library/Application Support/Blender/[version]/scripts/addons/`

1. Restart Blender again the addon will show up in `Edit->Preferences->Add-ons`.

1. Enable the addon.

## Debugging

1. Read [Debugging Python code with PyCharm](https://code.blender.org/2015/10/debugging-python-code-with-pycharm) to get started with Blender addon debugging. **NOTE:** With Blender 2.80+, you need the [updated debugger script](https://github.com/ux3d/random-blender-addons/blob/master/remote_debugger.py)

## Releases

Releases are available on the [downloads page](https://github.com/AnalyticalGraphicsInc/cesium-ion-blender-addon/releases) and are performed as needed. To perform a release, follow the following steps:

__Create the release package__

1. Pull down the latest master branch: `git pull origin master`
1. Modify `__init__.py` and increment the minor version only:
  - `"version": (1, 0, 0),` becomes `"version": (1, 1, 0),`
1. Proofread and update CHANGES.md to capture any changes since last release.
1. Commit and push these changes directly to master.
1. Make sure the repository is clean `git clean -d -x -f`. __This will delete all files not already in the repository.__
1. Run `python3 utils.py package` inside the root folder to build `io-cesium-ion-vx.x.x.zip` (were x.x.x will be the version)

__Testing__

_If any file fails to export or fails in an unintended way stop the release process and notify the team of the issue._

1. Install the newly packaged addon using the [installation guide](https://cesium.com/docs/tutorials/integrating-with-blender/). If there are any changes needed in the instructions, write an issue.
1. Launch Blender
1. Test Login Process
  - Authorize through user preferences.
  - Logout through user preferences.
  - Authorize through user preferences **but deny**.
  - Logout through user preferences.
  - Authorize through side-panel.
1. Export the `.blender` files contained within [test-assets](https://github.com/AnalyticalGraphicsInc/cesium-ion-blender-addon/tree/master/test-assets) using the options set within each file.

__Release__

Once all tests have pass, we can actually publish the release.

1. Create and push a tag, e.g.,
  - `git tag -a 1.1 -m '1.1 release'`
  - `git push origin 1.1` (do not use `git push --tags`)
1. Publish the release zip file to GitHub
 - [Create new release](https://github.com/AnalyticalGraphicsInc/cesium-ion-blender-addon/releases/new).
 - Select the tag you use pushed
 - Enter `Cesium ion Blender Addon 1.x` for the title
 - Include date, list of highlights and link to CHANGES.md (https://github.com/AnalyticalGraphicsInc/cesium-ion-blender-addon/blob/1.xx/CHANGES.md) as the description
 - Attach the `io-cesium-ion-vx.x.x.zip` you generated during the build process.
 - Publish the release
1. Tell the outreach team about the new release to have it included in the monthly release announcements/blog post and on social media.
1. Update cesium.com with a link to the latest release zip.
