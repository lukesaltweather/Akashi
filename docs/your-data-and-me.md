# Your Data and Me

For the sake of transparency I thought it would be a good idea to outline what data I have access to, and what data I store.

## You and your ID

Everything in Discord has a numerical ID: Users, Channels, Messages, Roles and even Emojis. This is _**public information**_. Everyone can see whichever IDs whenever they want to, provided they can right-click on the Object they want the ID of.  
It's as easy as going to the settings and enabling Developer Mode. 

IDs are used internally to get fetch more information on Members, like Avatars and Nicknames for Messages in \#file-room, or to mention specific roles.

## What I store

The only information on you that's permanently stored is your MemberID unique to Nekyou, and your Username. **Nothing else.**

Avatar-URLs, Nicknames, and other things are discarded after they've been processed. The bot has an internal cache in which it stores things like the Members, Servers and Messages it has access to. This is done to increase speed, so the bot doesn't have to call the API for everything, and can get that information from the local cache instead. This is done by virtually every bot. This information isn't stored permanently. Upon restart, the cache is deleted and filled up again.

The bot has access to all information a normal user has. It reads every message you send, and it has to in order to process commands. It tracks role updates, so it can automatically add new staff to the database. As mentioned earlier, this data is not kept.

## Can I delete my Data?

You may request deletion of your Username, however information about the work you have done cannot be removed. Please message lukesaltweather\#5374 if you want your data to be deleted.

