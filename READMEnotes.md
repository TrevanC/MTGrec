

Overall project scope - 
    Given a magictcg decklist for the EDH format, recommend cards to add

1 minute pitch:
    Magic the gathering cards can be complicated, and in the EDH format each deck is made up of 100 unique cards
    Currently there is no automated tool to assist in the deckbuilding process
    the goal of this project is to provide a tool that can evalute an entire decklist and provide advice and recommendations


split the project into multiple portions
    Card-tagger:
    available card data is limited to surface level information and unprocessed string text, need a way to better evaluate individual cards
    this part of the project helps with tagging specific functionality and categorizes cards in a more useful way
    information can be used to create an algorithm to recommend cards

    Deck-lists:
    another approach is a recommender algorithm using existing decklists from public community resources
    automated web-scraping of decklists from existing websites

    card-rec:
    the actual tool to be used in the form of a website, including front end and back end, db, recommendation algorithm(not done)

learned
    for the tagging part of the project I worked with an LLM to process the data on a large scale ??
        - developed taxonomy in order to target specific 
            - schema - 7 categories
                - taxonomy - 
        - describe taxonomy, how we got here
        - iterative process of working with ai to develop taxonomy
        - actual tagging process - utilized llm to automate
            - which needs the taxonomy + definitions

        - so the important part was developing the taxonomy

        prove the work is done + evidence
        - tagging on large scale within a contrained time period:
            - show taxonomy details
            - running LLM tagging in batch / parallel scripts running
            - 20$ of prompts processed
            - specifics

    in order to collect deck-list data, learned how to web-scrape (elaborate)
        - q: why we did things the way we did
        - goal: collect bulk decklist data to see what community consensus is / shared patterns among similar criteria (i.e. commander)
        - archidekt is the only website that publicly provides their API
        - API call to get decklist data, still need a way to compile decklist IDs to call
        - used web-scraping to gather hundreds of decklist IDs
        - then automated decklist collection - needed to add politeness delay to avoid getting cut off

    for the actual recommendation tool, learned how to setup front-end and back-end website basics?
        - UI for the front-end inspired by other magic-the gathering related websites and tools
            - decklist input, decklist display, summarized deck information
        - backend deals with processing decklist input and fetching corresponding card objects from database
            - database sourced from scryfall api
        - recommendation invokes recommendation algorithm
            - for now, recommender system (collaborative filtering)
                - if enough other people share the same choices, then recommend based on that
            - future - algorithm based on tags / synergy

    - add screenshots for the app, spending, parts of the process
        - breakdown of data
            - jupyter notebook for analysis or something
            -  screenshots etc
    - 


Problems:
    - large dataset - 30-40k unique cards + cardtext
    - criteria to add - how to evaluate cards

This part of the project:
    - use "tagging' system to categorize and evaluate cards on a larger scale
    - automate processing cards in bulk 

GOAL: Want to "tag" magic cards en masse so that I can then evaluate decklists and overall strategies

Plan:
    - collect card data via scryfall api
    - break down card text in order to categorize and label functionality - "tag" it
    - result - database of cards with interpreted text and useful information on the broader functionality of the card

Process:
    - create a shared taxonomy and schema as a way to structure and categorize card information
        - taxonomy should cover as many cases/types as possible since card evaluation/extraction process is a single pass through

    - issue - some functions of cards difficult to evaluate purely based on text content:
    i.e. using pure regex or text extraction cannot evaluate the functionality of the card
    - idea - use LLM instead, better understands context and meaning of sentences

    - issue - using an LLM takes time and money, size of dataset means processing every card
    - solution - limit processing targets to tags/types that are difficult to parse without an LLM, simpler functions can be extracted using non-LLM techniques
        - additionally, batch process cards so that multiple can be evaluated per prompt

current setup:
    - taxonomy, schema used to help provide context to LLM model for extracting specific tags from cards
        - schema defines the tagged card object and categories of tags
        - taxonomy defines the possible tags per category

    - tool is run through terminal commands, simply define color identity of cards and rate/size of batch

results:
    - created database including every commander-legal magic the gathering card and its tags
    - 

todo:
    - identify remaining functions of each card without use of LLM
    - use tagged cards to evaluate decklists in other portion of project
