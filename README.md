# largeLanguageOracle
Local setup:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PERPLEXITY_API_KEY=<your_perplexity_api_key>
python main.py
```


Fetching real market resolutions:
```
python fetch_market_resolution.py x
eg: python fetch_market_resolution.py 0x0FC5D2B61B29D54D487ACBC27E9694CEF303A9891433925E282742B1DBA4F399              
```


Generating sample data from block 68853567 to latest and storing in output_file.json:
```
python fetch_open_market_Ids.py 68853567 output_file.json
```