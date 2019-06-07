# Development
## Setup
1. `git clone git@github.com:AnalyticalGraphicsInc/ion-blender-exporter.git` - Clone the repository
1. Create a symlink from `./io-cesium-ion` to the your platform specific addon directory *(see below)*. The symlink be  similar to `[Blender Path]/addons/io-cesium-ion`.
    - **Windows:** `C:\Program Files\Blender Foundation\blender\[version]\addons`
    - **OSX:** `Users/[USER]/Library/Application Support/Blender/[version]/scripts/addons/`

## Debugging
- [Debug with PyCharm](https://code.blender.org/2015/10/debugging-python-code-with-pycharm) **NOTE:** If you are using Blender 2.80, you need the [updated debugger script](https://github.com/ux3d/random-blender-addons/blob/master/remote_debugger.py)
- [Debug with VSCode](DEBUGGING.md)

## Release
Releases are available on the [downloads page](https://github.com/AnalyticalGraphicsInc/ion-blender-exporter/releases). There is no release manager; instead, our community shares the responsibility.  Any committer can create the release for a given month, and at any point, they can pass the responsibility to someone else, or someone else can ask for it.  This spreads knowledge, avoids stratification, avoids a single point of failure, and is beautifully unstructured.
### Package
1. Pull the latest version of master. *(i.e. `git pull origin master`)*
1. Check that the projects version in `__init__.py` has been increased to reflect major or minor releases.
    * We use the version scheme `1.0` where the `1` is adding features and `0` is bug fixes.
    * The utils script will check for an increased version number upon packaging but it is good practice to check the version number is increased on your own.
1. Check that [globals.py](https://github.com/AnalyticalGraphicsInc/ion-blender-exporter/blob/master/globals.py) has the correct parameters.
    * Ensure that `LOCAL = FALSE`
1. Run `python3 utils.py package` inside the root folder to build `io-cesium-ion-v0.0.zip`
### Testing
_If any file fails to export or fails in an unintended way the release process is stopped and a issue is created._
1. Install the newly packaged project using the installation instructions found in the [README](https://github.com/AnalyticalGraphicsInc/ion-blender-exporter#installation).
1. Launch blender
1. Test Login Process
    1. Authorize through user preferences.
    1. Logout through user preferences.
    1. Authorize through user preferences **but deny**.
    1. Authorize through side-panel. (if option is not there something went wrong)
1. Export the `.blender` files contained within [test-assets](https://github.com/AnalyticalGraphicsInc/ion-blender-exporter/tree/master/test-assets) using the options set within each file.
### Release
1. Go to the [create new release](https://github.com/AnalyticalGraphicsInc/ion-blender-exporter/releases/new) page.
1. Edit the Options for the release page
    - **Tag Version**, and **Release Title** should match the suffix of `io-cesium-ion-v0.0.zip`.
         - For `io-cesium-ion-v0.0.zip` the tag would be `v0.0`
    - In the release add a change-log detailing what has been added. This should be as simple as copying the change-log from the merged pull requests.
1. Upload the packaged file (ie `io-cesium-ion-v0.0.zip`) that was created in the packaging step.
1. Publish the release
1. Ensure the new release is included in the monthly CesiumJS release announcement/blog post.
