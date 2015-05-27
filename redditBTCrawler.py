from requests import HTTPError
import praw
import webbrowser
import string
import datetime
import time
import itertools
import sys
import os
import re
import bitcoinaddress as btcAdr
import sqlite3


def createDataset(r,access_information, subreddits, startDate=(datetime.datetime.now()-datetime.timedelta(days=7)).strftime('%y%m%d%H%M%S'),
                  endDate=datetime.datetime.now().strftime('%y%m%d%H%M%S'), nCommentsPerSubmission=100, 
                  fineScale=12, nPostsPerFineScale=200):
    """
    :param r: reddit object
    :param access_information: access info from Oauth login
    :param subreddits: list of subreddits to grab
    :param startDate: start date in format yymmddHHMMSS
    :param endDate: end date in format yymmddHHMMSS
    :param nCommentsPerSubmission: number of comments to grab per submission. Default is 100.
    :param dbName: base of database name
    :param fineScale: scale of database in hours
    :param nPostsPerFineScale: number of posts per fine scale
    :return:
    """
    access_information = access_information
    # initialize database and Table
    dbFile= 'btcRedDb.db'
    conn = sqlite3.connect(dbFile)
    cursor = conn.cursor()
    tableNameWithParams= "usernames(username TEXT, btcAddress TEXT, commentID TEXT, daDate TEXT)"
    table= "usernames(username, btcAddress, commentID, daDate)"
    cursor.execute("CREATE TABLE IF NOT EXISTS " + tableNameWithParams)
    # loop through each subreddit
    subCount=1

    for subTerm in subreddits:
        sub= r.get_subreddit(subTerm)
        print 'Processing subreddit: ' + str(subCount)
        subCount+=1
        # get submissions within the date range
        matchingPosts = getAllPostsWithinRangeFineScale(sub, startDate=startDate, endDate=endDate, fineScale=fineScale,
                                                        nPostsPer=nPostsPerFineScale)
        # loop through each post and get top comments
        already_done=set()
        postCount=1
        countAddr=1
        for post in matchingPosts:
            print 'Processing post: ' + str(postCount)
            postCount+=1
            # get comments
            numTries = 0
            gotComments = False
            while not gotComments and numTries < 10:
                try:
                    comments = getCommentsFromSubmission(post, nCommentsPerSubmission)
                    gotComments = True
                except HTTPError:
                    time.sleep(2)
                    numTries += 1
            if addressInText(post.selftext):
                print 'Found address # ' +str(countAddr)
                countAddr+= 1
                author= str(post.author)
                knownAddr=  addressInText(post.selftext)
                
                sqlQuery= "INSERT INTO " + table+ " VALUES (?,?,?,?)"
                try:
                   # Execute the SQL command
                   cursor.execute(sqlQuery,(author, knownAddr,str(post.id), str(post.created)))
                   # Commit your changes in the database
                   conn.commit()
                   print 'added to db'
                except Exception as e:
                   
                   print str(e)
            #add comments to file
            if gotComments==True:
                print 'got the comments'
                for comment in comments:
                    if comment.id not in already_done:
                        already_done.add(comment.id)
                        if addressInText(comment.body):
                            print 'Found address # ' +str(countAddr)
                            countAddr+= 1
                            author= str(comment.author)
                            knownAddr=  addressInText(comment.body)
                            
                            sqlQuery= "INSERT INTO " + table+ " VALUES (?,?,?,?)"
                            try:
                               # Execute the SQL command
                               cursor.execute(sqlQuery,(author, knownAddr,str(comment.id), str(comment.created)))
                               # Commit your changes in the database
                               conn.commit()
                               print 'added to db'
                            except Exception as e:
                               
                               print str(e)

    print ('\nData collection complete!')


def getSubreddits(r, subredditNames):
    """
    :param r: reddit object
    :param subredditNames: list of subreddit names to retrieve
    :return: generator object of subreddit objects
    """

    for sub in subredditNames:
        yield r.get_subreddit(sub.lower())


def getRecentSubmissions(subreddit, dateRange):

    try:
        # perform an empty search to get all submissions within date range
        searchResult = subreddit.search('', period=dateRange, limit=None)
    except HTTPError:
        time.sleep(2)
        searchResult = getRecentSubmissions(subreddit, dateRange)

    # return search result
    return searchResult


def getCommentsFromSubmission(submission, nCommentsPerSubmission):
    try:
        submission.replace_more_comments(limit=16, threshold=10)
        flatComments = praw.helpers.flatten_tree(submission.comments)
    except Exception as e:
        if 'invalid_token' in str(e):
            r.refresh_access_information(access_information['refresh_token'])
        print 'Error: ' + str(e)
        time.sleep(1)
        flatComments= getCommentsFromSubmission(submission,nCommentsPerSubmission)
    # get comment list
    

    # filter list and return
    return flatComments[:nCommentsPerSubmission]


def getAllPostsWithinRangeFineScale(subreddit, startDate, endDate, fineScale=12, nPostsPer=1000):
    """
    Grabs posts using fine scale to grab maximum number
    :param fineScale: scale in hours. Default is 12.
    :param subreddit: subreddit object
    :param startDate: start date in format yymmdd
    :param endDate: end date in format yymmdd
    :param nPostsPer: number of posts per unit
    :return:
    """

    # create datetime object for each date
    startDateObject = datetime.datetime.strptime(startDate, "%y%m%d%H%M%S")
    endDateObject = datetime.datetime.strptime(endDate, "%y%m%d%H%M%S")

    # get posts
    posts = []
    tempStart = startDateObject
    while True:

        # get temporary end date
        tempEnd = tempStart + datetime.timedelta(hours=fineScale)

        # check if tempEnd is after than endDateObject
        if (tempEnd - endDateObject) > datetime.timedelta(0, 0, 0):
            # set tempEnd to be endDateObject
            tempEnd = endDateObject

        # break if start is after end
        if (tempStart - tempEnd) > datetime.timedelta(0, 0, 0):
            break

        # convert to strings
        tempStartStr = tempStart.strftime('%y%m%d%H%M%S')
        tempEndStr = tempEnd.strftime('%y%m%d%H%M%S')

        # get posts within range
        tempPosts = getPostsWithinRange(subreddit, tempStartStr, tempEndStr, nPosts=nPostsPer)

        # combine with posts
        posts = itertools.chain(posts, tempPosts)

        # iterate on start date
        tempStart = tempEnd + datetime.timedelta(seconds=1)

    # return
    return posts


def getPostsWithinRange(subreddit, startDate, endDate, nPosts=1000):
    """
    :param subreddit: subreddit object
    :param startDate: start date in format yymmddHHMMSS
    :param endDate: end date in format yymmddHHMMSS
    :return: generator object of posts
    """
    # convert dates to unix time format
    startDate = time.mktime(datetime.datetime.strptime(startDate, "%y%m%d%H%M%S").timetuple())
    endDate = time.mktime(datetime.datetime.strptime(endDate, "%y%m%d%H%M%S").timetuple())

    # generate timestamp search term
    searchTerm = 'timestamp:' + str(startDate)[:-2] + '..' + str(endDate)[:-2]

    # get posts
    try:
        posts = subreddit.search(searchTerm, sort='top', syntax='cloudsearch', limit=nPosts)
    except HTTPError:
        print 'sleep team son'
        time.sleep(2)
        posts = getPostsWithinRange(subreddit, startDate, endDate, nPosts=nPosts)

    return posts


def addressInText(text):
    #gets rid of candidates that are too small and cleans for punctuation
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    possibleKeys= [regex.sub('', x) for x in text.split() if len(x)>23]
    keys=[]
    for x in possibleKeys:
        if btcAdr.validate(x)== True:
            keys.append(x)
    if len(keys)>0:
        return ', '.join(keys)
    else:
        return False


def login(accessInfoKey):
    r = praw.Reddit('redditBTCrawler' 'https://insertyoursitehere.com')
    # input your Oauth app info, leave the redirect_uri as is
    r.set_oauth_app_info(client_id='yourClientID',
                             client_secret='yourClientSecret',
                             redirect_uri='http://127.0.0.1:65010/'
                                          'authorize_callback')
    
    scope= ['read','identity']
    url = r.get_authorize_url('enter any random uniquelycreatedkey', scope, True)
    webbrowser.open(url)
    access_information = r.get_access_information(accessInfoKey)
    return [r,access_information]


if __name__ == "__main__":

    # handle arguments, dates are yymmddHHMMSS
    startDate= str(140501010000)
    endDate= str(141231010000)
    fineScale = int(8) 
    #take key from http header
    accessInfoKey= 'put the part after &code= ' 
    # initialize reddit object
    loginList=login(accessInfoKey)
    r=loginList[0]
    access_information=loginList[1]
    subreddits=['Bitcoin','BTC']
    createDataset(r,access_information, subreddits, startDate=startDate, endDate=endDate, fineScale=fineScale)