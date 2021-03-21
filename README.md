# plover_cards

A Plover plugin which helps you build an Anki deck from the words and phrases you have typed.

## Usage

Make sure Anki isn't already running.

### Options

| Option                            | What it's used for                                                                                                                                                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Anki Collection                   | The Anki collection with existing cards, which will be ignored when building cards                                                                                           |
| Card Type                         | The card type for existing cards, which will be ignored when building cards                                                                                                  |
| Ignore File                       | Where to save the list of words to ignore                                                                                                                                    |
| Output File                       | Where to save the CSV file of new cards, which can  then be imported into Anki                                                                                               |
| Clear output file before starting | Clear the output file when you press start. You'll want this on if you have imported the cards from the previous session, and off if you're continuing the previous session. |

These options are saved in `{your_plover_config_folder}/plover_cards.cfg`

### Building Screen

- *Stroke list*: Pick which stroke you want on the back of the Anki card here.
- *Card list*:
  - *Translation*: The word or phrase on the front of the Anki card.
  - *Stroke*: The stroke on the back of the Anki card.
  - *Similar ignored*: Similar words that are either already in the Anki deck or have been added to the ignore list.
- *Buttons*:
  - **Clear**: Clear the chosen stroke. Useful if you want to skip this card, since by default it will choose the first stroke in the list.
  - **Ignore**: Add this word/phrase to the ignore list. It won't appear next time you use the card builder.
  - **<**: Go to previous card.
  - **>**: Go to next card.
  - **Finish**: Finish building cards.
