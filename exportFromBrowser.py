# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior arthur@milchior.fr
# encoding: utf8
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Feel free to contribute to this code on https://github.com/Arthur-Milchior/anki-export-from-browser
# Add-on number NNNNNNNN https://ankiweb.net/shared/info/NNNNNNNN

import re
import os
import time
from PyQt5.QtWidgets import QAction

from aqt import mw
from aqt.exporting import ExportDialog
from aqt.qt import QKeySequence, QPushButton, QDialogButtonBox, QDialog
from aqt.utils import tooltip, showInfo, getSaveFile, checkInvalidFilename, showWarning

from anki import Collection
from anki.exporting import Exporter, AnkiExporter, exporters
from anki.hooks import addHook, remHook
from anki.lang import ngettext
from anki.utils import ids2str


def debug(t):
    print(t)
    pass

#Change to ExportDialog
oldInit=ExportDialog.__init__
def __init__(self,mw,did=None,cids=None):
    self.cids = cids
    oldInit(self,mw,did=did)
ExportDialog.__init__=__init__

# oldExporterChanged = ExportDialog.exportChanged
# def exporterChanged(self, idx):
#     oldExporterChanged(self,idx)
# ExportDialog.exportChanged=exporterChanged


def setup(self, did):
        """
        keyword arguments:
        did -- if None, then export whole anki. If did, export this deck. If list of cids, expots those cids.
        """
        debug(f"Calling setup({did}), its cids is {self.cids}")
        self.exporters = exporters()
        # if a deck specified, start with .apkg type selected
        idx = 0
        if did or self.cids:
            for c, (k,e) in enumerate(self.exporters):
                if e.ext == ".apkg":
                    idx = c
                    break
        self.frm.format.insertItems(0, [e[0] for e in self.exporters])
        self.frm.format.setCurrentIndex(idx)
        self.frm.format.activated.connect(self.exporterChanged)
        self.exporterChanged(idx)
        # deck list
        self.decks = [_("All Decks")] 
        if self.cids:
            bs=_("Browser's selection")
            debug(f"Adding {bs}")
            self.decks = self.decks+[bs]
        self.decks = self.decks + sorted(self.col.decks.allNames())
        self.frm.deck.addItems(self.decks)
        # save button
        b = QPushButton(_("Export..."))
        self.frm.buttonBox.addButton(b, QDialogButtonBox.AcceptRole)
        # set default option if accessed through deck button
        if did:
            name = self.mw.col.decks.get(did)['name']
            index = self.frm.deck.findText(name)
            self.frm.deck.setCurrentIndex(index)
        if self.cids:
            self.frm.deck.setCurrentIndex(1)
ExportDialog.setup=setup

def accept(self):
        debug(f"Calling accept()")
        self.exporter.includeSched = (
            self.frm.includeSched.isChecked())
        self.exporter.includeMedia = (
            self.frm.includeMedia.isChecked())
        self.exporter.includeTags = (
            self.frm.includeTags.isChecked())
### Starting change 
        if self.frm.deck.currentIndex() == 0:#position 0 means: all decks.
            self.exporter.did = None
            self.exporter.cids = None 
        elif self.frm.deck.currentIndex() == 1 and self.cids is not None:#position 1 means: selected decks.
            self.exporter.did = None
            self.exporter.cids = self.cids
        else:
            self.exporter.cids = None 
### ending change 
            name = self.decks[self.frm.deck.currentIndex()]
            self.exporter.did = self.col.decks.id(name)
        if self.isVerbatim:
            name = time.strftime("-%Y-%m-%d@%H-%M-%S",
                                 time.localtime(time.time()))
            deck_name = _("collection")+name
        else:
            # Get deck name and remove invalid filename characters
            deck_name = self.decks[self.frm.deck.currentIndex()]
            deck_name = re.sub('[\\\\/?<>:*|"^]', '_', deck_name)

        if not self.isVerbatim and self.isApkg and self.exporter.includeSched and self.col.schedVer() == 2:
            showInfo("Please switch to the regular scheduler before exporting a single deck .apkg with scheduling.")
            return

        filename = '{0}{1}'.format(deck_name, self.exporter.ext)
        while 1:
            file = getSaveFile(self, _("Export"), "export",
                               self.exporter.key, self.exporter.ext,
                               fname=filename)
            if not file:
                return
            if checkInvalidFilename(os.path.basename(file), dirsep=False):
                continue
            break
        self.hide()
        if file:
            self.mw.progress.start(immediate=True)
            try:
                f = open(file, "wb")
                f.close()
            except (OSError, IOError) as e:
                showWarning(_("Couldn't save file: %s") % str(e))
            else:
                os.unlink(file)
                exportedMedia = lambda cnt: self.mw.progress.update(
                        label=ngettext("Exported %d media file",
                                       "Exported %d media files", cnt) % cnt
                        )
                addHook("exportedMediaFiles", exportedMedia)
                self.exporter.exportInto(file)
                remHook("exportedMediaFiles", exportedMedia)
                period = 3000
                if self.isVerbatim:
                    msg = _("Collection exported.")
                else:
                    if self.isTextNote:
                        msg = ngettext("%d note exported.", "%d notes exported.",
                                    self.exporter.count) % self.exporter.count
                    else:
                        msg = ngettext("%d card exported.", "%d cards exported.",
                                    self.exporter.count) % self.exporter.count
                tooltip(msg, period=period)
            finally:
                self.mw.progress.finish()
        QDialog.accept(self)
ExportDialog.accept = accept

# Changes to Exporter

oldCardIds= Exporter.cardIds
def cardIds(self):
    debug(f"Calling cardIds()")
    if self.cids is not None:
        debug(f"cids: {self.cids}, returning it")
        return self.cids
    else:
        r=oldCardIds(self)
        debug(f"cids: {self.did}, returning {r}")
        return r
Exporter.cardIds = cardIds
    
def setupMenu(browser):
    debug(f"Calling setupMenu() from exportFromBrowser")
    a = QAction("Export selection", browser)
    a.setShortcut(QKeySequence("Ctrl+Shift+E"))
    a.triggered.connect(lambda : ExportDialog(mw,cids=browser.selectedCards()))
    browser.form.menuEdit.addAction(a)

addHook("browser.setupMenus", setupMenu)

def exportInto(self, path):
    #Needed to change this to ensure it uses cardIds !
    
        # sched info+v2 scheduler not compatible w/ older clients
        self._v2sched = self.col.schedVer() != 1 and self.includeSched

        # create a new collection at the target
        try:
            os.unlink(path)
        except (IOError, OSError):
            pass
        self.dst = Collection(path)
        self.src = self.col
        # find cards
        cids = self.cardIds()#ONLY CHANGE !!!!
        # copy cards, noting used nids
        nids = {}
        data = []
        for row in self.src.db.execute(
            "select * from cards where id in "+ids2str(cids)):
            nids[row[1]] = True
            data.append(row)
            # clear flags
            row = list(row)
            row[-2] = 0
        self.dst.db.executemany(
            "insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            data)
        # notes
        strnids = ids2str(list(nids.keys()))
        notedata = []
        for row in self.src.db.all(
            "select * from notes where id in "+strnids):
            # remove system tags if not exporting scheduling info
            if not self.includeSched:
                row = list(row)
                row[5] = self.removeSystemTags(row[5])
            notedata.append(row)
        self.dst.db.executemany(
            "insert into notes values (?,?,?,?,?,?,?,?,?,?,?)",
            notedata)
        # models used by the notes
        mids = self.dst.db.list("select distinct mid from notes where id in "+
                                strnids)
        # card history and revlog
        if self.includeSched:
            data = self.src.db.all(
                "select * from revlog where cid in "+ids2str(cids))
            self.dst.db.executemany(
                "insert into revlog values (?,?,?,?,?,?,?,?,?)",
                data)
        else:
            # need to reset card state
            self.dst.sched.resetCards(cids)
        # models - start with zero
        self.dst.models.models = {}
        for m in self.src.models.all():
            if int(m['id']) in mids:
                self.dst.models.update(m)
        # decks
        if not self.did:
            dids = []
        else:
            dids = [self.did] + [
                x[1] for x in self.src.decks.children(self.did)]
        dconfs = {}
        for d in self.src.decks.all():
            if str(d['id']) == "1":
                continue
            if dids and d['id'] not in dids:
                continue
            if not d['dyn'] and d['conf'] != 1:
                if self.includeSched:
                    dconfs[d['conf']] = True
            if not self.includeSched:
                # scheduling not included, so reset deck settings to default
                d = dict(d)
                d['conf'] = 1
            self.dst.decks.update(d)
        # copy used deck confs
        for dc in self.src.decks.allConf():
            if dc['id'] in dconfs:
                self.dst.decks.updateConf(dc)
        # find used media
        media = {}
        self.mediaDir = self.src.media.dir()
        if self.includeMedia:
            for row in notedata:
                flds = row[6]
                mid = row[2]
                for file in self.src.media.filesInStr(mid, flds):
                    # skip files in subdirs
                    if file != os.path.basename(file):
                        continue
                    media[file] = True
            if self.mediaDir:
                for fname in os.listdir(self.mediaDir):
                    path = os.path.join(self.mediaDir, fname)
                    if os.path.isdir(path):
                        continue
                    if fname.startswith("_"):
                        # Scan all models in mids for reference to fname
                        for m in self.src.models.all():
                            if int(m['id']) in mids:
                                if self._modelHasMedia(m, fname):
                                    media[fname] = True
                                    break
        self.mediaFiles = list(media.keys())
        self.dst.crt = self.src.crt
        # todo: tags?
        self.count = self.dst.cardCount()
        self.dst.setMod()
        self.postExport()
        self.dst.close()
AnkiExporter.exportInto= exportInto
