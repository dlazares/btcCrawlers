# BTCrawlers

BTCrawlers lets you crawl Reddit or Github for Bitcoin Addresses

  - Reddit- Search by date range
   * A modified version of Ari Morcos' RedditDataset
   
  - Github- get all bitcoin addresses in readme files




### Version
1.0

### Dependencies

BTCrawlers uses the following to work properly:

* Requests
* Praw
* sqlite3
* bitcoinaddress


## How to use RedditBTCrawler
* Install Dependencies
* Create OAuth application on Reddit

Add your info to login:

```sh
r = praw.Reddit('redditBTCrawler' 'https://insertyoursitehere.com')
    # input your Oauth app info, leave the redirect_uri as is
    r.set_oauth_app_info('',
                             client_secret='',
                             redirect_uri='http://127.0.0.1:65010/'
                                          'authorize_callback')
```

Change Date range and Subreddits you'd like to search through and
* fineScale should be lowered for very popular subreddits

```sh
# dates are yymmddHHMMSS
    startDate= str(140101010000)
    endDate= str(140105010000)
    fineScale = int(8) 
    subreddits=['Bitcoin','BTC']
```

Third, run program and you will encounter an OAuth error:
read  https://praw.readthedocs.org/en/v2.1.21/pages/oauth.html
For step 4, take code and put it in accessInfoKey.

Run program

## How to use GitBTCrawler

* Install Dependencies
* Run Program


