# plover_cards

A Plover plugin which helps you make cards for flashcard programs like Anki.

![screenshot of card builder window](https://user-images.githubusercontent.com/3298461/119559105-264b1480-bd9a-11eb-8509-c2e97e1bafbc.png)

## Table of Contents
- [Setup](#setup)
- [Plover Cards Hook](#plover-cards-hook)
- [Card Builder](#card-builder)
- [ANKI_ADD_CARD Command](#anki_add_card-command)

## Setup

- Enable "plover_cards_hook"
  - Right click the Plover icon, "Configure", "Plugins" tab, check the box next to "plover_cards_hook", "Apply"

### For Anki integration:

- Install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) plugin for [Anki](https://apps.ankiweb.net/). You may need to restart Anki for the plugin to take effect

## Plover Cards Hook

This part of the plugin listens to what you write and records the suggestions (you don't need to have the suggestion window open). It'll keep a count of how many times you use a stroke so you can focus on only the words you use often (or least often). Unlike the suggestions window, it'll also record suggestions for command, prefix and suffix strokes if you use them.

The data is stored in `{your_plover_config_folder}/plover_cards/card_suggestions.pickle`. This gets saved when you disable the extension, quit Plover and every 5 minutes.

## Card Builder

This is where you can look at the suggestions and choose which ones to make into flashcards.

### Usage

#### Anki Integration

- Make sure Anki is running in the background

#### Opening

- (from the menu) Right click the Plover icon, "Tools", "Card Builder"
- (from the gui) Click "Card Builder" icon in the top bar of the main Plover window

### Settings

| Option            | What it's used for                                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Use Ignore File   | Whether to keep a file for words to ignore                                                                              |
| Ignore File       | Path to the ignore file, which is a text file with each word/phrase to ignore on a new line                             |
| Compare to Anki   | Whether to find words/phrases to ignore from existing Anki cards                                                        |
| Query             | Which cards to look at, for example `deck:Plover` and `note:Steno`. The syntax is [the same as in the Anki browser][1]. |
| Compare Field     | Which field in the card to look at, for example "Translation" or "Front"                                                |
| Output to CSV     | Whether to output to CSV, which can be imported into Anki or other programs like Excel                                  |
| Output File       | Path to the output file, which is a CSV of `Translation,Strokes`                                                        |
| Write Method      | Whether to append or overwrite the output file                                                                          |
| Add to Anki       | Whether to add cards to Anki at the end                                                                                 |
| Deck              | Which deck to add to                                                                                                    |
| Note Type         | What type of note to add                                                                                                |
| Translation Field | Which field to put the translation in                                                                                   |
| Strokes Field     | Which field to put the strokes in                                                                                       |
| Tags              | Space separated list of tags to add to the new cards                                                                    |

[1]: https://docs.ankiweb.net/searching.html

These options are saved in `{your_plover_config_folder}/plover_cards.cfg`.

### Build Cards

#### Card list
You can click on any of the following columns to sort by that column. Click again to change the sort order.

You can hide columns by right clicking the header and selecting/deselecting columns.

You can change the column size by dragging the edges of the column title.

  - **Count**: The number of times you typed this word and/or the number of times it was suggested to you
  - **Count (shorter)**: The number of times the program found a shorter suggestion for what you typed
  - **Last Used**: The date and time you last used this word
  - **Translation**: The word or phrase on the front of the Anki card
  - **Stroke**: The stroke on the back of the Anki card
  - **Similar ignored**: Similar words that are either already in the Anki deck or have been added to the ignore list

#### Stroke list
 Pick which stroke you want on the back of the Anki card here. Alternatively, write your stroke in the box underneath to use something else.
#### Buttons
  - **Clear**: Clear the chosen stroke. Useful if you want to skip this card, since by default it will choose the first stroke in the list
  - **Ignore**: Add this word/phrase to the ignore list. It won't appear next time you use the card builder. This button is unavailable if "Use Ignore File" is not selected
  - **<**: Go to previous card
  - **>**: Go to next card
  - **Finish**: Finish building cards. Depending on your settings, it will output to CSV and/or add cards to anki

## ANKI_ADD_CARD Command

You can add dictionary entries to add cards to Anki.

`{PLOVER:ANKI_ADD_CARD}` will open up the Anki Add Cards window with the last used word and a list of stroke suggestions.

`{PLOVER:ANKI_ADD_CARD:X}` will do the same but for the last `X` words.

It will use the same settings as in the "Add to Anki" section in the card builder (deck, note_type, translation_field, strokes_field, tags).
