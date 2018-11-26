# Export cards selected in the Browser
## Rationale
Sometime, I want to export only some notes. And the cards are not all
in the same deck. I wanted to be able to just select cards in the
browser and export them. Thus, this add-on is here.
## Usage
Open the Browser, select the cards you want to export. Then go to
Edit>Export selection (Ctrl+Shift+E), and the standard exporting
window will open, but with a new options: "Browser's
selection". Keeping this option, you can export your selection as you
exported decks.

## Warning
Note that you are exporting cards, and not notes. Image that you
select a card and don't select it's sibling. Then you import it (into
another profile probably, or another computer). Only the selected card
will be imported. When Anki detect that some siblings are missing, it
will generate it as a new card. Thus its entire review history will be
missing.

Note that, even without this add-on, the same problem may occur if an
exported card has a sibling which is not exported, i.e. a sibling
which does not belong to the exported deck.

## Internal
This add-on change
* in ```aqt.exporting```, the method ```ExportDialog.__init__```. The new
  method calls the previous version of the method.
* in ```aqt.exporting```, the methods ```ExportDialog.setup```,
  ```ExportDialog.accept```. The new methods do not call the previous
  version of the method.
* in ```anki.exporting```, the method ```Exporter.cardIds``` is
  modified. The former version of the method is called if the exporter
  is called from the browser with a non-empty selection.
* in ```anki.exporting```, the method ```AnkiExporter.exportInto``` is
  redefined, not calling the previous version. A single line is changed.
## Todo 
Correct the warning.

## Version 2.0
Sorry, but no such version, unless someone wants to pay for it. 

## Links, licence and credits

Key         |Value
------------|-------------------------------------------------------------------
Copyright   | Arthur Milchior <arthur@milchior.fr>
Based on    | Anki code by Damien Elmes <anki@ichi2.net>
License     | GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
Source in   | https://github.com/Arthur-Milchior/anki-export-from-browser
Addon number| [1983204951](https://ankiweb.net/shared/info/1983204951)
