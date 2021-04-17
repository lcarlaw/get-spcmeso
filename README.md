# get-spcmeso
Simple script to download SPC Mesoanalysis images.

Nothing fancy; just enough to grab pertinent images for post-event recaps and
analysis. Additional parameters can be added to the `parms.py` file.

## Useage
```
python main.py START_TIME END_TIME [-d DOMAIN]
```

* `START_TIME`: First hour of archived data to download. Form is `YYYY-mm-dd/HH`.

* `END_TIME`: First hour of archived data to download. Form is `YYYY-mm-dd/HH`.

* `DOMAIN`: Numerical domain value (at the end of the SPC mesoanalysis url). Defaults to 20.

Log files will be updated in the `./logs` directory and output will save to the `./downloads` directory.

This script will initialize up to 6 concurrent threads to download the requested images.
