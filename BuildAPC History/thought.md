
What I need to do with the json file:
* read it into a dataframe
  * can't do it all at once, the dataframe (not the file) is too big for the memory I've got
      * `read_json(line=True, chunksize=size)` solves this

What I need to do with the initial dataframe:
* only focus on the parts of it I need
  * `frame = frame[columns]`
* iterate through the subframe chunks
* Get only the rows which have a table in the selftext

What I'm going to need to do with the selftext:
* ignore everything that's not the table
* possibly choose between multiple tables?
  * think the first go round should just find the first table, maybe expand to this later
* extract the table
  * regex?
  * readtable with options?
* turn table into columns


Things I want to check for when reading the build table:
* probably only want to look at US data to avoid currency issues
  * possible expansion at a later point though

