# chessdotcom-crawler
A crawler for exploring player profiles on [chess.com](https://www.chess.com/home) and saving them to a MySQL database.

## Getting started
Before running the crawler you need to do a few things:
- Clone/download the repo
- Create a conda environment with the correct packages by running `conda create --file chess-crawler.yml` in the root folder of the repo OR run `python setup.py install` in the base folder to install the `chess_crawler` package (this should install all the necessary packages also)
- Install [MySQL](https://dev.mysql.com/downloads/installer/) and make a MySQL database called `chess_crawler`. You can choose a different name, but will need to change it in `main.py` also, line 15 `engine =...`. On the same line also need to provide username and password for an account with access to the database.

After that can run `python main.py` in the `/chess_crawler/src` folder to run the crawler.

## Structure of program
The idea is to define a pipeline for the crawler (an instance of the Crawler class) to process each player: the crawler is given a `GetterPipeline` that is used to get data, `DiscriminatorPipeline` for deciding if player data should be saved, and a `SaverPipeline` to save the player data if needed. The crawler also needs some strategy for picking the next player to look at based on the current player - this is provided by a `PlayerSelector` object. 

## Main classes
### `crawler.py`
Main classes used to crawl through data and save it to file. Used to compose other classes into a single object.

### `discriminators.py`
Used for deciding if the data for a given player should be saved in the database, e.g. based on if they've played enough matches.

### `getters.py`
Classes for objects that get different types of data. The data is fetched either using the chess.com API or scraping directly from HTML on chess.com.

### `player.py`
Class used for storing player data temporarily.

### `player_selectors.py`
Classes used for selecting the next player for the crawler to look at

### `savers.py`
Classes for saving player data into the SQL database

### `utils.py`
Utility functions, e.g. for deleting duplicate entries from a database.
