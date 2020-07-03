# -*- coding: cp1252 -*-
'''
EXIF Summarizer v1.0
Created on Nov 01, 2011

This script scans a directory (shallow or recursive) looking for image files
and extracts information from EXIF metadata.
It is particularly useful to list all the involved cameras.

The EXIF extraction requires the "pyexiv2" library (http://tilloy.net/dev/pyexiv2/)


(C)opyright 2011 Fabio Sangiacomo <fabio.sangiacomo _at_ digital-forensics.it>
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

import sys, os, datetime, pyexiv2, string, webbrowser
from optparse import OptionParser
from os.path import join
##from googlegantt import GanttChart, GanttCategory

################################################################################
# Camera obj definition
class Camera:

    # init
    def __init__(self, make, model, date, filename):
        # if invalid params are passed, sets attributes to invalid values
        self.camera_make = make or "EMPTY"
        self.camera_model = model or "EMPTY"
        self.counter = 1
        self.fnamelist = [filename]
        if date == "":
            # oldest set to max and newest set to min:
            # ----> this allows future updates
        self.oldest = date or datetime.datetime.max
        self.newest = date or datetime.datetime.min

    # comparison operator
    def __cmp__(self, other):
        if self.camera_make == other.camera_make:
            if self.camera_model == other.camera_model:
                return 0
        return 1
            
################################################################################
# MAIN
def main(argv):

    # parser options
    parser = OptionParser()
    parser.add_option("-i", "--indir", dest="indirectory", help="input folder name to scan")
    parser.add_option("-o", "--outfile", dest="outfilename", help="output file name (no extension)")
    parser.add_option("-r", "--recursive", action="store_true", dest="rec", default=False, help="goes recursive into directories")
    parser.add_option("-f", "--filelist", action="store_true", dest="flist", default=False, help="add photos list to the report")
##    parser.add_option("-t", "--timeline", action="store_true", dest="timel", default=False, help="add cameras usage timeline to the web report")
    parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, help="create Comma-Separated Values Output File")
    parser.add_option("-w", "--web", action="store_true", dest="web", default=False, help="create HTML Output File")
    (options, args) = parser.parse_args()

    # checks for the input folder name presence
    if options.indirectory is None:
        parser.print_help()
        sys.exit(1)
    else:
        indir = options.indirectory

    # checks if the input folder name is an actual directory
    if not os.path.isdir(indir):
        parser.print_help()
        print("Please specify a folder name for -i option!")
        sys.exit(1)

    # checks if at least an output format was selected
    if options.csv == options.web == False:
        parser.print_help()
        print("Please specify at least an output format!")
        sys.exit(1)

    # reset global counter of processed items
    global count
    count = 0

    # warnings logfile
    global warn, warnings
    warn = open("exifsum.log",'w');
    warnings = 0

    # scan all the files contained into the directory (shallow or recursive)
    try:
        if options.rec:
            for root, dirs, files in os.walk(indir):
                for fname in files:
                    process_file(join(root,fname),options)
        else:
            files = os.listdir(indir)
            for fname in files:
                process_file(join(indir,fname),options)
                
    except KeyboardInterrupt:
        print("\nScanning interrupted by keyboard")

    ##------------------------------------------------------------------------##
    # output
    cfile = wfile = None
    outfile = options.outfilename or "exif_summarizer_output"

    ##----------
    # csv output
    if options.csv:
        cfile = open('%s.csv' % outfile,'wb')
        cfile.write('Make,Model,#photos,Oldest(Exif.Image.DateTimeOriginal),Newest(Exif.Image.DateTimeOriginal)\n')
        for i in camera_list:
            cfile.write('{},{},{},{},{}\n'.format(i.camera_make, i.camera_model, i.counter, i.oldest, i.newest))

        # file list compiled optionally
        if options.flist:
            cfile.write('--------------------------------------------------------------------------------\n')
            cfile.write('Make,Model,Filename\n')
            for i in camera_list:
                for f in i.fnamelist:
                    cfile.write('{},{},{}\n'.format(i.camera_make, i.camera_model, f))
                    
        cfile.close()
        
    ##----------
    # html output
    if options.web:
##        # makes optionally a Gantt chart to view the usage interval of the cameras
##        if options.timel:
##            gch = 100 + 8*len(camera_list)
##            gc = GanttChart('EXIF Summarizer Timeline', width=700, height=gch)
##            low = GanttCategory('Low Usage (<100)', '0c0')
##            mid = GanttCategory('Mid Usage (<500)', 'fc0')
##            high = GanttCategory('High Usage (>500)', 'c00')
            
        wfile = open('%s.html' % outfile,'wb')
        # writes page header
        wfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n')
        wfile.write('"http://www.w3.org/TR/html4/loose.dtd">\n')
        wfile.write('<html><head><title>{}</title>\n'.format(outfile))
        wfile.write('<meta name="GENERATOR" content="EXIF Summarizer 1.0">\n')
        # adds page style
        wfile.write(css_style)
 
        # adds javascript to make the tables sortable
        wfile.write('\n<script type="text/javascript">\n')
        wfile.write(sortable)
        wfile.write('</script>\n\n')
        wfile.write('</head><body>\n')

        # writes 1st table header
        wfile.write('<h2 style=\'display:inline\'>EXIF summarizer v1.0 </h2><p style=\'display:inline\'>has found the following cameras...</p><br><br>\n')
        wfile.write('<table class="sortable" id="cameras" border="1" cellpadding="2" cellspacing="0">\n')
        wfile.write('<thead>\n')
        wfile.write('<tr>\n')
        wfile.write('<th>Make</th>\n')
        wfile.write('<th>Model</th>\n')
        wfile.write('<th># Photos</th>\n')
        wfile.write('<th>Oldest (Photo - DateTimeOriginal)</th>\n')
        wfile.write('<th>Newest (Photo - DateTimeOriginal)</th>\n')
        wfile.write('</tr>\n')
        wfile.write('</thead>\n')
        
        empty_make_model = 0
        # writes 1st table content
        wfile.write('<tbody>\n')
        for i in camera_list:
            if i.camera_make == 'EMPTY' or i.camera_model == 'EMPTY':
                empty_make_model = 1
            wfile.write('<tr>\n')
            wfile.write('<td>{}</td>\n'.format(i.camera_make))
            wfile.write('<td>{}</td>\n'.format(i.camera_model))
            wfile.write('<td>{}</td>\n'.format(i.counter))
            if i.oldest == datetime.datetime.max:
                wfile.write('<td>N/A</td>\n')
            else:
                wfile.write('<td>{}</td>\n'.format(i.oldest))
            if i.newest == datetime.datetime.min:
                wfile.write('<td>N/A</td>\n')
            else:
                wfile.write('<td>{}</td>\n'.format(i.newest))

##            if options.timel:
##                if i.oldest != datetime.datetime.max and i.newest != datetime.datetime.min:
##                    if i.counter > 500:
##                        curr_cat = high
##                    elif i.counter > 100:
##                        curr_cat = mid
##                    else:
##                        curr_cat = low
##                    gc.add_task(i.camera_model, i.oldest.date(), i.newest.date(),category=curr_cat)
                
            wfile.write('</tr>\n')
        wfile.write('</tbody>\n')
        # writes 1st table footer
        wfile.write('</table>\n')
        
        wfile.write('<p>Total number of processed photos: <b>{}</b></p>\n'.format(count))
        wfile.write('<p>Total number of identified cameras: <b>{}</b></p>\n'.format(len(camera_list)-empty_make_model))

        # file list compiled optionally
        if options.flist:
            wfile.write('<br>\n')
            # writes 2nd table header
            numrow = 0
            wfile.write('<h3>List of photos for each camera</h3>\n')
            wfile.write('<table class="sortable" id="photos" border="1" cellpadding="2" cellspacing="0">\n')
            wfile.write('<thead>\n')
            wfile.write('<tr>\n')
            wfile.write('<th>Camera Make</th>\n')
            wfile.write('<th>Camera Model</th>\n')
            wfile.write('<th class="unsortable">File Name</th>\n')
            wfile.write('</tr>\n')
            wfile.write('</thead>\n')

            # writest 2nd table content
            wfile.write('<tbody>\n')
            for i in camera_list:
                for f in i.fnamelist:
                    wfile.write('<tr>\n')
                    wfile.write('<td>{}</td>\n'.format(i.camera_make))
                    wfile.write('<td>{}</td>\n'.format(i.camera_model))
                    wfile.write('<td><a href="file:///{}">{}</a></td>\n'.format(f, f))
                    wfile.write('</tr>\n')
            wfile.write('</tbody>\n')
            # writes 2nd table footer
            wfile.write('</table>\n')

##        # optionally inserts gantt image
##        if options.timel:
##            #url = gc.get_url()
##            try:
##                image = gc.get_image('timel.png')
##                wfile.write('<img src="timel.png" alt="EXIF summarizer timeline" />\n')
##            except:
##                warnings += 1
##                warn.write('\nGoogle Chart limits exceeded! Timeline is not shown!\n')
        
        # writes page footer
        if warnings > 0:
            wfile.write('<p><b>{}</b> warnings are occured. Check the <a href="exifsum.log">logfile</a>!\n'.format(warnings))

        wfile.write('</body></html>\n')
        wfile.close()
        webbrowser.open('%s.html' % outfile)

    # END
    warn.close()    
    print('\nProcess ended with {} warnings.'.format(warnings))
  

################################################################################
# function to process a single file
def process_file(filename,options):

    global count    
    global curr_camera
    curr_camera = 0

    # If the input filename represents a folder, skip it
    if os.path.isdir(filename) == True:
        return
    
    # Checks if the current file belongs to the admitted extensions list
    if os.path.splitext(filename.lower())[1] in extList:
        res = exif_info_extraction(filename)
    else:
        return

    # skip the image if the metadata extraction has failed
    if res == False:
        return

    # updates processes items counter
    count += 1
    sys.stdout.write("Processed files: %s\r" % count)
    
    # DEBUG print
    # print filename
    # print '{},{},{}'.format(curr_camera.camera_make,curr_camera.camera_model,curr_camera.oldest)    
    # print "-------------------------------------"
    # DEBUG print end

    # checks if curr_camera is already in camera_list
    # if already present -> updates the entry
    if curr_camera in camera_list:
        tmp_entry = camera_list.index(curr_camera)
        camera_list[tmp_entry].counter += 1
        camera_list[tmp_entry].fnamelist.append(filename)
        try:
            if curr_camera.oldest < camera_list[tmp_entry].oldest:
                camera_list[tmp_entry].oldest = curr_camera.oldest
            if curr_camera.newest > camera_list[tmp_entry].newest:
                camera_list[tmp_entry].newest = curr_camera.newest
        except TypeError:
            global warn, warnings
            warn.write("\nWarning: 'Photo.DateTimeOriginal' field doesn't respect EXIF standard in file %s\n" % filename)
            warnings += 1
            
    # else append the new camera
    else:
        # print("\nNew entry {}".format(curr_camera.camera_model))
        camera_list.append(curr_camera)
        

################################################################################
# function to extract exif metadata
def exif_info_extraction(filename):

    global curr_camera
    curr_camera = 0

    # tries to extract metadata from passed filename
    meta = pyexiv2.ImageMetadata(filename)
    try:
        meta.read()
    except IOError:
        global warn, warnings
        warn.write("\nWarning: EXIF metadata extraction has failed in file %s\n" % filename)
        warnings += 1
        return False

    # init variables
    tagMake = tagModel = tagDate = ""
    
    # composes a Camera obj
    if 'Exif.Image.Make' in meta.exif_keys:
        tagMake = meta['Exif.Image.Make'].value
    if 'Exif.Image.Model' in meta.exif_keys:
        tagModel = meta['Exif.Image.Model'].value
    if 'Exif.Photo.DateTimeOriginal' in meta.exif_keys:
        tagDate = meta['Exif.Photo.DateTimeOriginal'].value

    curr_camera = Camera(tagMake,tagModel,tagDate,filename)
    
    return True

##### GLOBAL variables #####  
# list of admitted file extensions (lowercase)
extList = [".jpg", ".jpeg", ".tiff"]
camera_list = []
curr_camera = 0
count = 0
warn = 0
warnings = 0

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
    background-color: #ff8;
}
tr.even {
    background-color: #ddd;
}
.hl {
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

