In order to use this script, you need:
  1) an ArchivesSpace instance with a repository and resource record
  2) a json file with records in the format described
  3) a secrets.py file with the ids for your repository and resource and your ArchivesSpace username, password, and base url

This file:
  1) loads the json file as a cache and ensures that the cache is working as a dictionary.
        if successful, the message "Cache load successful." will print.

  2) Prompts the user to "delete all records."
        If the user inputs 'yes' or 'y', all top containers, digital object, and archival object records will be deleted.
            The program will print each response objects showing status and ids.
        -->this functionality is meant for TESTING ONLY. 

  3) Prompts the user to "Add data."
        If the user inputs 'yes' or 'y', the program will iterate through the json dictionary, compile records, and post them to  the archivesspace instance.
            Each response object will be printed, showing status, ids, uris, and warnings.
        Any other input will cause the program to exit.
