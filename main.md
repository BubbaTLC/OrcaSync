# Orca Sync

Orca sync is a tool dessigned to sync Orca Profiles between multiple machines using git as a backend.

Files ares stored within a git repository, allowing users to push and pull changes to their Orca setup easily.

It is recommended to use a private repository to ensure that your configurations and profiles remain secure.

It is also recomended that you nbame your branches according to the machine names you use, to avoid conflicts when syncing between multiple devices.


## Profile Storage Locations

| Operating System | Default User Profile Path                                                         | Default System Profile Path                              | Notes                                                                                                                                                                                    |
| ---------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Windows          | `C:\Users\<username>\AppData\Roaming\OrcaSlicer\user\` (or `user{10digitnumber}`) | `C:\Users\<username>\AppData\Roaming\OrcaSlicer\system\` | AppData is a hidden folder. User profiles are JSON files within subfolders (filament, machine, process).                                                                                 |
| macOS            | `~/Library/Application Support/OrcaSlicer/user/`                                  | `~/Library/Application Support/OrcaSlicer/system/`       | Library is a hidden folder. Bundled system profiles can also be found by right-clicking the Orca app, then Show Contents &gt; Contents &gt; Resources &gt; Profiles.                     |
| Linux            | `~/.config/OrcaSlicer/user/`                                                      | `~/.config/OrcaSlicer/system/`                           | .config is a hidden folder. AppImage versions typically use this path. Some Flatpak installations may use `/home/<user name>/.var/app/io.github.softfever.OrcaSlicer/config/OrcaSlicer`. |
| Portable Version | `(Custom data_dir or --datadir option)`                                           | `(Custom data_dir or --datadir option)`                  | If a data\_dir folder exists under the application's path, Orca uses it. The --datadir command line option allows specifying any custom location.                                        |

## Installation

Orca Sync can be installed <> Use the following command to install it:

```bash
example command
```

Orca Sync must be installed on all machines that will be syncing Orca profiles.

## Configuration

Configure Orca Sync by editing the `orca-sync-config.yaml` file located in the Orca Sync installation directory.

| Configname      | Values | Notes |
| --------------- | ------ | ----- |
| repository_name |        |       |
| repository_url  |        |       |
| branch_prefix   |        |       |
| branch_postfix  |        |       |
| user_paths      |        |       |
| sync_interval   |        |       |