# Akashi - a short guide to get you started

## The basics

Akashi is a bot made to keep track of all our chapters. The driving idea behind development: using it shouldn't feel like a chore. This guide will give you some basic information about how to use the bot, as the learning curve might be just a little too steep in the beginning. But trust me, it's super easy once you get used to how it works.

{% hint style="info" %}
#### The bot has an inbuilt help command `($help)` with descriptions and the parameters the commands accept, or even require sometimes. Use it as a reference if you're unsure of how to run a command.
{% endhint %}

Commands always have to be structured in a certain way. Let's have a look at this general example first:

{% code title="Yes, this is actually works. Try it out with different breeds!" %}
```text
$cat -breed=bengal
```
{% endcode %}

A command generelly accepts all the parameters \(you can also think of them as options or settings of the command\) specified in the help file, regardless of how many you enter. They always start with a dash `-` and are separated from their value through the equal sign `=`. The parameters marked _required_  **have** to be included, the command won't work otherwise. 

{% hint style="success" %}
Parameters _**always**_ start with a dash `-` and are _**always**_ separated by their value through the equal sign `=`. 
{% endhint %}

It should be kept in mind that a value ends either with the next dash, or when the command ends. What does this mean for us?

{% code title="command example 1" %}
```text
$addproject -title=Yankee-kun and the white cane girl -link=https://google.com
```
{% endcode %}

The value of the parameter `title` is in this case `Yankee-kun and the white cane girl`. This works with anything, numbers, URLs, 

{% hint style="warning" %}
as long as there's no dash with a space in front of it.
{% endhint %}

Don't worry though, if something is off about the command structure the command will just fail to execute.

## Summary

You now know how to structure your commands so that you can actually start writing ones by yourself. The next chapter will go into more detail on how to use the bot in practice!

