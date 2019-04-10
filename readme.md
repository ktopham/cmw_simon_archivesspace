In order to use this script, you need:
  1) an ArchivesSpace instance with a repository and resource record
  2) a json file with records in the format described
  3) a secrets.py file with the ids for your repository and resource and your ArchivesSpace username, password, and base url

When you run this file:
  1) it will load the json file as a cache and ensure that the cache is working as a dictionary
        if successful, the message "Cache load successful." will print

  2) it will ask you if you want to "delete all records"
        if you input 'yes' or 'y', all top containers, digital object, and archival object records will be deleted
            the program will print each response objects showing status and ids
        -->this functionality is meant for testing only

  3) it will prompt you to add data
        if you input 'yes' or 'y', the program will iterate through the json dictionary, compile records, and post them to archivesspace
            the program will print each response objects showing status, ids, uris, and warnings
        any other input will cause the program to exit
