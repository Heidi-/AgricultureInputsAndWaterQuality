## AgricultureInputsAndWaterQuality

Project to bring together USDA data on agricultural chemical inputs (fertilizer and pesticide) and USGS water quality monitoring results in a user-friendly app. Initial focus on Oregon, may expand in the future.

## Usage

Classes QueryNASS and QueryNAWQA in Query.py provide an interface to pull data from the USDA's NASS quickstats api and the USGS's National Water-Quality Assesment Program. Note that the NASS API requires a key. The query object can be initialized with a string of either the key itself, or a path to a file containing only the key.:

    nass = Query.QueryNASS("KEY-HERE")
    - or -
    nass = Query.QueryNASS("path/to/file.txt")
