# sas-esm-work
---

To create an executable using PyInstaller with UPX compression, run the following command:

```bash
pyinstaller --onefile get_work.py --upx-dir "path\to\upx-4.2.3-win64"
```

UPX can be found [here](https://github.com/upx/upx/releases/download/v4.2.3/upx-4.2.3-win64.zip).

The result should look like:

![SAS Work Pie Chart](https://raw.githubusercontent.com/robertocosta-sas/sas-esm-work/main/sas_work_usage.png "SAS Work Pie Chart")

