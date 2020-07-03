# -*- coding: cp1252 -*-
'''
WhatsApp Extractor v1.0
Created on Dec 10, 2011

This script opens the msgstore.db WhatsApp SQLite database and creates
a report with the contacts and the conversations for each contact.

(C)opyright 2011 Fabio Sangiacomo <fabio.sangiacomo@digital-forensics.it>
Released under MIT licence

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

'''

import sys, os, string, datetime, sqlite3, webbrowser
from optparse import OptionParser

################################################################################
# Chatsession obj definition
class Chatsession:

    # init
    def __init__(self,pkcs,contactname,contactid,contactmsgcount):

        # if invalid params are passed, sets attributes to invalid values
        # primary key
        self.pk_cs = pkcs or -1
        # contact nick
        self.contact_name = contactname or "EMPTY"
            
        # contact id
        self.contact_id = contactid or "EMPTY"
        # contact msg counter
        self.contact_msg_count = contactmsgcount or -1

        # chat session messages
        self.msg_list = []

    # comparison operator
    def __cmp__(self, other):
        if self.pk_cs == other.pk_cs:
                return 0
        return 1

################################################################################
# Message obj definition
class Message:

    # init
    def __init__(self,pkmsg,fromme,msgdate,text,contactfrom,contactto):

        # if invalid params are passed, sets attributes to invalid values
        # primary key
        self.pk_msg = pkmsg or -1
        # "from me" flag
        self.from_me = fromme or -1
        # message timestamp
        if msgdate == "":
            self.msg_date = "N/A"
        else:
            self.msg_date = datetime.datetime.fromtimestamp(int(msgdate)+11323*60*1440)
        # message text
        self.msg_text = text or "EMPTY"
        # message sender
        self.contact_from = contactfrom or "EMPTY"
        # message receiver
        self.contact_to = contactto or "EMPTY"

    # comparison operator
    def __cmp__(self, other):
        if self.pk_msg == other.pk_msg:
                return 0
        return 1

            
################################################################################
# MAIN
def main(argv):

    chat_session_list = []

    # parser options
    parser = OptionParser()
    parser.add_option("-i", "--infile", dest="infile", help="input 'msgstore.db' file to scan")
    (options, args) = parser.parse_args()

    # checks for the input file
    if options.infile is None:
        parser.print_help()
        sys.exit(1)
    if not os.path.exists(options.infile):
        print('"{}" file is not found!'.format(options.infile))
        sys.exit(1)

    # connects to the database
    msgstore = sqlite3.connect(options.infile)
    c = msgstore.cursor()

    # gets all the chat sessions
    try:
        c.execute("SELECT * FROM ZWACHATSESSION")
        for chats in c:
            curr_chat = Chatsession(chats[0],chats[10],chats[8],chats[6])
            chat_session_list.append(curr_chat)
    except sqlite3.Error as msg:
        print('Error: {}'.format(msg))
        sys.exit(1)

    # for each chat session, gets all messages
    for chats in chat_session_list:
        try:
            c.execute("SELECT * FROM ZWAMESSAGE WHERE ZCHATSESSION=?;", str(chats.pk_cs))
            for msgs in c:
                curr_message = Message(msgs[0],msgs[3],msgs[9],msgs[10],msgs[12],msgs[11])
                chats.msg_list.append(curr_message)

        except sqlite3.Error as msg:
            print('Error: {}'.format(msg))
            sys.exit(1)

    # gets the db owner id
    try:
        c.execute("SELECT ZFROMJID FROM ZWAMESSAGE WHERE ZISFROMME='1'")
        try:
            owner = (c.fetchone()[0]).split('/')[0]
        except:
            owner = "NotAvailable"
    except sqlite3.Error as msg:
        print('Error: {}'.format(msg))
        sys.exit(1)

    # OUTPUT
    wfile = open('%s.html' % owner,'wb')
    # writes page header
    wfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n')
    wfile.write('"http://www.w3.org/TR/html4/loose.dtd">\n')
    wfile.write('<html><head><title>{}</title>\n'.format(owner))
    wfile.write('<meta name="GENERATOR" content="WhatsApp Extractor v1.0">\n')
    # adds page style
    wfile.write(css_style)
    
    # adds javascript to make the tables sortable
    wfile.write('\n<script type="text/javascript">\n')
    wfile.write(sortable)
    wfile.write('</script>\n\n')
    wfile.write('</head><body>\n')

    # writes 1st table header "CHAT SESSION"
    wfile.write('<h2>{} chat sessions</h2>\n'.format(owner))
    wfile.write('<table class="sortable" id="chatsession" border="1" cellpadding="2" cellspacing="0">\n')
    wfile.write('<thead>\n')
    wfile.write('<tr>\n')
    wfile.write('<th>PK</th>\n')
    wfile.write('<th>Contact Name</th>\n')
    wfile.write('<th>Contact ID</th>\n')
    wfile.write('<th># Messages</th>\n')
    wfile.write('</tr>\n')
    wfile.write('</thead>\n')
    
    # writes 1st table content
    wfile.write('<tbody>\n')
    for i in chat_session_list:
        wfile.write('<tr>\n')
        wfile.write('<td>{}</td>\n'.format(i.pk_cs))
        wfile.write('<td class="contact"><a href="#{}">{}</a></td>\n'.format(i.contact_name,i.contact_name))
        wfile.write('<td class="contact">{}</td>\n'.format(i.contact_id))
        wfile.write('<td>{}</td>\n'.format(i.contact_msg_count))
        wfile.write('</tr>\n')
    wfile.write('</tbody>\n')
    # writes 1st table footer
    wfile.write('</table>\n')

    # writes a table for each chat session
    for i in chat_session_list:
        wfile.write('<h3>Chat session # {}: <a name="{}">{}</a></h3>\n'.format(i.pk_cs, i.contact_name, i.contact_name))
        wfile.write('<table class="sortable" id="msg_{}" border="1" cellpadding="2" cellspacing="0">\n'.format(i.contact_id.split('@')[0]))
        wfile.write('<thead>\n')
        wfile.write('<tr>\n')
        wfile.write('<th>PK</th>\n')
        wfile.write('<th>From</th>\n')
        wfile.write('<th>To</th>\n')
        wfile.write('<th>Msg content</th>\n')
        wfile.write('<th>Msg date</th>\n')
        wfile.write('</tr>\n')
        wfile.write('</thead>\n')

        # writes table content
        wfile.write('<tbody>\n')
        for y in i.msg_list:                                
            if y.from_me == 1:
                wfile.write('<tr class="me">\n')
            else:
                wfile.write('<tr class="other">\n')
            wfile.write('<td>{}</td>\n'.format(y.pk_msg))
            try:
                wfile.write('<td class="contact">{}</td>\n'.format(y.contact_from.split('/')[0]))
            except:
                wfile.write('<td class="contact">N/A</td>\n')
            try:
                wfile.write('<td class="contact">{}</td>\n'.format(y.contact_to.split('/')[0]))
            except:
                wfile.write('<td class="contact">N/A</td>\n')                    
            try:
                wfile.write('<td class="text">{}</td>\n'.format(y.msg_text.encode('latin-1')))
            except:
                wfile.write('<td class="text">N/A</td>\n')                    
            wfile.write('<td>{}</td>\n'.format(y.msg_date))
            wfile.write('</tr>\n')
        wfile.write('</tbody>\n')
        # writes 1st table footer
        wfile.write('</table>\n')

    # writes page footer        
    wfile.write('</body></html>\n')
    wfile.close()

    #END
    webbrowser.open('%s.html' % owner)            
 

##### GLOBAL variables #####
css_style = """
<style type="text/css">
body {
    font-family: calibri;
}
h1 {
    font-style:italic;
}
h2 {
    font-style:italic;
}
h3 {
    font-style:italic;
}
table {
    text-align: center;
}
th {
    font-style:italic;
}
td.text {
    width: 600px;
    text-align: left;
}
td.contact {
    width: 250px;
}
tr.even {
    background-color: #ddd;
}
tr.me {
    background-color: #8f8;
}
tr.other {
    background-color: #fff;
}
</style>
"""

sortable = """
/*
Table sorting script  by Joost de Valk, check it out at http://www.joostdevalk.nl/code/sortable-table/.
Based on a script from http://www.kryogenix.org/code/browser/sorttable/.
Distributed under the MIT license: http://www.kryogenix.org/code/browser/licence.html .

Copyright (c) 1997-2007 Stuart Langridge, Joost de Valk.

Version 1.5.7
*/

/* You can change these values */
var image_path = "http://www.joostdevalk.nl/code/sortable-table/";
var image_up = "arrow-up.gif";
var image_down = "arrow-down.gif";
var image_none = "arrow-none.gif";
var europeandate = true;
var alternate_row_colors = true;

/* Don't change anything below this unless you know what you're doing */
addEvent(window, "load", sortables_init);

var SORT_COLUMN_INDEX;
var thead = false;

function sortables_init() {
	// Find all tables with class sortable and make them sortable
	if (!document.getElementsByTagName) return;
	tbls = document.getElementsByTagName("table");
	for (ti=0;ti<tbls.length;ti++) {
		thisTbl = tbls[ti];
		if (((' '+thisTbl.className+' ').indexOf("sortable") != -1) && (thisTbl.id)) {
			ts_makeSortable(thisTbl);
		}
	}
}

function ts_makeSortable(t) {
	if (t.rows && t.rows.length > 0) {
		if (t.tHead && t.tHead.rows.length > 0) {
			var firstRow = t.tHead.rows[t.tHead.rows.length-1];
			thead = true;
		} else {
			var firstRow = t.rows[0];
		}
	}
	if (!firstRow) return;
	
	// We have a first row: assume it's the header, and make its contents clickable links
	for (var i=0;i<firstRow.cells.length;i++) {
		var cell = firstRow.cells[i];
		var txt = ts_getInnerText(cell);
		if (cell.className != "unsortable" && cell.className.indexOf("unsortable") == -1) {
			cell.innerHTML = '<a href="#" class="sortheader" onclick="ts_resortTable(this, '+i+');return false;">'+txt+'<span class="sortarrow">&nbsp;&nbsp;<img src="'+ image_path + image_none + '" alt="&darr;"/></span></a>';
		}
	}
	if (alternate_row_colors) {
		alternate(t);
	}
}

function ts_getInnerText(el) {
	if (typeof el == "string") return el;
	if (typeof el == "undefined") { return el };
	if (el.innerText) return el.innerText;	//Not needed but it is faster
	var str = "";
	
	var cs = el.childNodes;
	var l = cs.length;
	for (var i = 0; i < l; i++) {
		switch (cs[i].nodeType) {
			case 1: //ELEMENT_NODE
				str += ts_getInnerText(cs[i]);
				break;
			case 3:	//TEXT_NODE
				str += cs[i].nodeValue;
				break;
		}
	}
	return str;
}

function ts_resortTable(lnk, clid) {
	var span;
	for (var ci=0;ci<lnk.childNodes.length;ci++) {
		if (lnk.childNodes[ci].tagName && lnk.childNodes[ci].tagName.toLowerCase() == 'span') span = lnk.childNodes[ci];
	}
	var spantext = ts_getInnerText(span);
	var td = lnk.parentNode;
	var column = clid || td.cellIndex;
	var t = getParent(td,'TABLE');
	// Work out a type for the column
	if (t.rows.length <= 1) return;
	var itm = "";
	var i = 0;
	while (itm == "" && i < t.tBodies[0].rows.length) {
		var itm = ts_getInnerText(t.tBodies[0].rows[i].cells[column]);
		itm = trim(itm);
		if (itm.substr(0,4) == "<!--" || itm.length == 0) {
			itm = "";
		}
		i++;
	}
	if (itm == "") return; 
	sortfn = ts_sort_caseinsensitive;
	if (itm.match(/^\d\d[\/\.-][a-zA-z][a-zA-Z][a-zA-Z][\/\.-]\d\d\d\d$/)) sortfn = ts_sort_date;
	if (itm.match(/^\d\d[\/\.-]\d\d[\/\.-]\d\d\d{2}?$/)) sortfn = ts_sort_date;
	if (itm.match(/^-?[£$Û¢´]\d/)) sortfn = ts_sort_numeric;
	if (itm.match(/^-?(\d+[,\.]?)+(E[-+][\d]+)?%?$/)) sortfn = ts_sort_numeric;
	SORT_COLUMN_INDEX = column;
	var firstRow = new Array();
	var newRows = new Array();
	for (k=0;k<t.tBodies.length;k++) {
		for (i=0;i<t.tBodies[k].rows[0].length;i++) { 
			firstRow[i] = t.tBodies[k].rows[0][i]; 
		}
	}
	for (k=0;k<t.tBodies.length;k++) {
		if (!thead) {
			// Skip the first row
			for (j=1;j<t.tBodies[k].rows.length;j++) { 
				newRows[j-1] = t.tBodies[k].rows[j];
			}
		} else {
			// Do NOT skip the first row
			for (j=0;j<t.tBodies[k].rows.length;j++) { 
				newRows[j] = t.tBodies[k].rows[j];
			}
		}
	}
	newRows.sort(sortfn);
	if (span.getAttribute("sortdir") == 'down') {
			ARROW = '&nbsp;&nbsp;<img src="'+ image_path + image_down + '" alt="&darr;"/>';
			newRows.reverse();
			span.setAttribute('sortdir','up');
	} else {
			ARROW = '&nbsp;&nbsp;<img src="'+ image_path + image_up + '" alt="&uarr;"/>';
			span.setAttribute('sortdir','down');
	} 
    // We appendChild rows that already exist to the tbody, so it moves them rather than creating new ones
    // don't do sortbottom rows
    for (i=0; i<newRows.length; i++) { 
		if (!newRows[i].className || (newRows[i].className && (newRows[i].className.indexOf('sortbottom') == -1))) {
			t.tBodies[0].appendChild(newRows[i]);
		}
	}
    // do sortbottom rows only
    for (i=0; i<newRows.length; i++) {
		if (newRows[i].className && (newRows[i].className.indexOf('sortbottom') != -1)) 
			t.tBodies[0].appendChild(newRows[i]);
	}
	// Delete any other arrows there may be showing
	var allspans = document.getElementsByTagName("span");
	for (var ci=0;ci<allspans.length;ci++) {
		if (allspans[ci].className == 'sortarrow') {
			if (getParent(allspans[ci],"table") == getParent(lnk,"table")) { // in the same table as us?
				allspans[ci].innerHTML = '&nbsp;&nbsp;<img src="'+ image_path + image_none + '" alt="&darr;"/>';
			}
		}
	}		
	span.innerHTML = ARROW;
	alternate(t);
}

function getParent(el, pTagName) {
	if (el == null) {
		return null;
	} else if (el.nodeType == 1 && el.tagName.toLowerCase() == pTagName.toLowerCase()) {
		return el;
	} else {
		return getParent(el.parentNode, pTagName);
	}
}

function sort_date(date) {	
	// y2k notes: two digit years less than 50 are treated as 20XX, greater than 50 are treated as 19XX
	dt = "00000000";
	if (date.length == 11) {
		mtstr = date.substr(3,3);
		mtstr = mtstr.toLowerCase();
		switch(mtstr) {
			case "jan": var mt = "01"; break;
			case "feb": var mt = "02"; break;
			case "mar": var mt = "03"; break;
			case "apr": var mt = "04"; break;
			case "may": var mt = "05"; break;
			case "jun": var mt = "06"; break;
			case "jul": var mt = "07"; break;
			case "aug": var mt = "08"; break;
			case "sep": var mt = "09"; break;
			case "oct": var mt = "10"; break;
			case "nov": var mt = "11"; break;
			case "dec": var mt = "12"; break;
			// default: var mt = "00";
		}
		dt = date.substr(7,4)+mt+date.substr(0,2);
		return dt;
	} else if (date.length == 10) {
		if (europeandate == false) {
			dt = date.substr(6,4)+date.substr(0,2)+date.substr(3,2);
			return dt;
		} else {
			dt = date.substr(6,4)+date.substr(3,2)+date.substr(0,2);
			return dt;
		}
	} else if (date.length == 8) {
		yr = date.substr(6,2);
		if (parseInt(yr) < 50) { 
			yr = '20'+yr; 
		} else { 
			yr = '19'+yr; 
		}
		if (europeandate == true) {
			dt = yr+date.substr(3,2)+date.substr(0,2);
			return dt;
		} else {
			dt = yr+date.substr(0,2)+date.substr(3,2);
			return dt;
		}
	}
	return dt;
}

function ts_sort_date(a,b) {
	dt1 = sort_date(ts_getInnerText(a.cells[SORT_COLUMN_INDEX]));
	dt2 = sort_date(ts_getInnerText(b.cells[SORT_COLUMN_INDEX]));
	
	if (dt1==dt2) {
		return 0;
	}
	if (dt1<dt2) { 
		return -1;
	}
	return 1;
}
function ts_sort_numeric(a,b) {
	var aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
	aa = clean_num(aa);
	var bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
	bb = clean_num(bb);
	return compare_numeric(aa,bb);
}
function compare_numeric(a,b) {
	var a = parseFloat(a);
	a = (isNaN(a) ? 0 : a);
	var b = parseFloat(b);
	b = (isNaN(b) ? 0 : b);
	return a - b;
}
function ts_sort_caseinsensitive(a,b) {
	aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]).toLowerCase();
	bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]).toLowerCase();
	if (aa==bb) {
		return 0;
	}
	if (aa<bb) {
		return -1;
	}
	return 1;
}
function ts_sort_default(a,b) {
	aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
	bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
	if (aa==bb) {
		return 0;
	}
	if (aa<bb) {
		return -1;
	}
	return 1;
}
function addEvent(elm, evType, fn, useCapture)
// addEvent and removeEvent
// cross-browser event handling for IE5+,	NS6 and Mozilla
// By Scott Andrew
{
	if (elm.addEventListener){
		elm.addEventListener(evType, fn, useCapture);
		return true;
	} else if (elm.attachEvent){
		var r = elm.attachEvent("on"+evType, fn);
		return r;
	} else {
		alert("Handler could not be removed");
	}
}
function clean_num(str) {
	str = str.replace(new RegExp(/[^-?0-9.]/g),"");
	return str;
}
function trim(s) {
	return s.replace(/^\s+|\s+$/g, "");
}
function alternate(table) {
	// Take object table and get all it's tbodies.
	var tableBodies = table.getElementsByTagName("tbody");
	// Loop through these tbodies
	for (var i = 0; i < tableBodies.length; i++) {
		// Take the tbody, and get all it's rows
		var tableRows = tableBodies[i].getElementsByTagName("tr");
		// Loop through these rows
		// Start at 1 because we want to leave the heading row untouched
		for (var j = 0; j < tableRows.length; j++) {
			// Check if j is even, and apply classes for both possible results
			if ( (j % 2) == 0  ) {
				if ( !(tableRows[j].className.indexOf('odd') == -1) ) {
					tableRows[j].className = tableRows[j].className.replace('odd', 'even');
				} else {
					if ( tableRows[j].className.indexOf('even') == -1 ) {
						tableRows[j].className += " even";
					}
				}
			} else {
				if ( !(tableRows[j].className.indexOf('even') == -1) ) {
					tableRows[j].className = tableRows[j].className.replace('even', 'odd');
				} else {
					if ( tableRows[j].className.indexOf('odd') == -1 ) {
						tableRows[j].className += " odd";
					}
				}
			} 
		}
	}
}
"""

if __name__ == '__main__':
    main(sys.argv[1:])

