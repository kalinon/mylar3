Runtime failure: refreshComic queued records without seriesyear, then formatted one placeholder with two values. Worker crashed KeyError seriesyear and HTTP response failed with 500. Third formatting defect affected multiple already-queued records.

Acceptance: python3 -m unittest discover -s tests -p test_api_refresh_contract.py -v
Deployment: build a derivative of the exact deployed image with only mylar/api.py replaced; retain old app config and native Mylar backup; use TrueNAS app.update preserving all other service settings; verify HTTP success and canonical missing issue creation.
