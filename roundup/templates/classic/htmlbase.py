 
# Do Not Edit (Unless You Want To)
# This file automagically generated by roundup.htmldata.makeHtmlBase
# 
fileDOTindex = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<tr>
    <property name="name">
        <td><display call="link('name')"></td>
    </property>
    <property name="type">
        <td><display call="plain('type')"></td>
    </property>
</tr>
"""

fileDOTnewitem = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<table border=0 cellspacing=0 cellpadding=2>

<tr class="strong-header">
  <td colspan=2>File upload details</td>
</td>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">File:</span></td>
    <td class="form-text"><input type="file" name="content" size="40"></td>
</tr>

<tr bgcolor="ffffea">
    <td>&nbsp;</td>
    <td class="form-text"><display call="submit()"></td>
</tr>

</table>
"""

issueDOTfilter = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<property name="title">
 <tr><th width="1%" align="right" class="location-bar">Title</th>
 <td><display call="field('title')"></td></tr>
</property>
<property name="status">
 <tr><th width="1%" align="right" class="location-bar">Status</th>
 <td><display call="checklist('status')"></td></tr>
</property>
<property name="priority">
 <tr><th width="1%" align="right" class="location-bar">Priority</th>
 <td><display call="checklist('priority')"></td></tr>
</property>
"""

issueDOTindex = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<tr class="row-<display call="plain('status')">">
    <property name="id">
        <td valign="top"><display call="plain('id')"></td>
    </property>
    <property name="activity">
        <td valign="top"><display call="reldate('activity', pretty=1)"></td>
    </property>
    <property name="priority">
        <td valign="top"><display call="plain('priority')"></td>
    </property>
    <property name="title">
        <td valign="top"><display call="link('title')"></td>
    </property>
    <property name="status">
        <td valign="top"><display call="plain('status')"></td>
    </property>
    <property name="assignedto">
        <td valign="top"><display call="link('assignedto')"></td>
    </property>
</tr>
"""

issueDOTitem = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<table border=0 cellspacing=0 cellpadding=2>

<tr class="strong-header">
  <td colspan=4>Item Information</td>
</td>

<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Title</span></td>
    <td colspan=3 class="form-text"><display call="field('title', size=80)"></td>
</tr>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Created</span></td>
    <td class="form-text"><display call="reldate('creation', pretty=1)">
        (<display call="plain('creator')">)</td>
    <td width=1% nowrap align=right><span class="form-label">Last activity</span></td>
    <td class="form-text"><display call="reldate('activity', pretty=1)"></td>
</tr>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Priority</span></td>
    <td class="form-text"><display call="field('priority')"></td>
    <td width=1% nowrap align=right><span class="form-label">Status</span></td>
    <td class="form-text"><display call="menu('status')"></td>
</tr>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Superseder</span></td>
    <td class="form-text"><display call="field('superseder', size=40, showid=1)"></td>
    <td width=1% nowrap align=right><span class="form-label">Nosy List</span></td>
    <td class="form-text"><display call="field('nosy')"></td>
</tr>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Change Note</span></td>
    <td colspan=3 class="form-text"><display call="note()"></td>
</tr>

<tr bgcolor="ffffea">
    <td>&nbsp;</td>
    <td colspan=3 class="form-text"><display call="submit()"></td>
</tr>

<tr class="strong-header">
    <td colspan=4><b>Messages</b></td>
</tr>
<property name="messages">
<tr>            
    <td colspan=4><display call="list('messages')"></td>
</tr>
</property>

<tr class="strong-header">
  <td colspan=4><b>Files</b></td>
</tr>
<tr class="form-help">
 <td colspan=4>
   <a href="newfile?:multilink=issue<display call="plain('id')">:files">Attach a file to this issue</a>
 </td>
</tr>
<property name="files">
 <tr>            
     <td colspan=4><display call="list('files')"></td>
 </tr>
</property>

</table>

"""

msgDOTindex = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<tr>
    <property name="date">
        <td><display call="link('date')"></td>
    </property>
    <property name="author">
        <td><display call="plain('author')"></td>
    </property>
    <property name="summary">
        <td><display call="plain('summary')"></td>
    </property>
</tr>
"""

msgDOTitem = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<table border=0 cellspacing=0 cellpadding=2>

<tr class="strong-header">
  <td colspan=2>Message Information</td>
</td>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Author</span></td>
    <td class="form-text"><display call="plain('author')"></td>
</tr>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Recipients</span></td>
    <td class="form-text"><display call="plain('recipients')"></td>
</tr>

<tr bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Date</span></td>
    <td class="form-text"><display call="plain('date')"></td>
</tr>

<tr bgcolor="ffeaff">
 <td colspan=2 class="form-text">
  <pre><display call="plain('content')"></pre>
 </td>
</tr>

<property name="files">
<tr class="strong-header"><td colspan=2><b>Files</b></td></tr>
<tr><td colspan=2><display call="list('files')"></td></tr>
</property>

<tr class="strong-header"><td colspan=2><b>History</b></td><tr>
<tr><td colspan=2><display call="history()"></td></tr>

</table>
"""

styleDOTcss = """h1 {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 18pt; 
  font-weight: bold; 
}

h2 {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 16pt; 
  font-weight: bold; 
}

h3 {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 12pt; 
  font-weight: bold; 
}

a:hover {  
  font-family: Verdana, Helvetica, sans-serif; 
  text-decoration: underline;
  color: #333333; 
}

a:link {
  font-family: Verdana, Helvetica, sans-serif; 
  text-decoration: none;
  color: #000099;
}

a {
  font-family: Verdana, Helvetica, sans-serif; 
  text-decoration: none;
  color: #000099;
}

p {
  font-family: Verdana, Helvetica, sans-serif;
  font-size: 10pt;
  color: #333333;
}

th {
  font-family: Verdana, Helvetica, sans-serif; 
  font-weight: bold;
  font-size: 10pt; 
  color: #333333;
}

.form-help {
  font-family: Verdana, Helvetica, sans-serif;
  font-size: 10pt;
  color: #333333;
}

.std-text {
  font-family: Verdana, Helvetica, sans-serif;
  font-size: 10pt;
  color: #333333;
}

.tab-small {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 8pt; 
  color: #333333;
}

.location-bar {
  background-color: #44bb66;
  color: #ffffff;
  border: none;
}

.strong-header {
  font-family: Verdana, Helvetica, sans-serif;
  font-size: 12pt;
  font-weight: bold;
  background-color: #000000;
  color: #ffffff;
}

.list-header {
  background-color: #aaccff;
  color: #000000;
  border: none;
}

.list-item {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 10pt; 
}

.list-nav {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 10pt; 
  font-weight: bold;
}

.row-normal {
  background-color: #ffffff;
  border: none;

}

.row-hilite {
  background-color: #efefef;
  border: none;
}

.row-unread {
  background-color: #ffddd9;
  border: none;
}

.row-in-progress {
  background-color: #3ccc50;
  border: none;
}

.row-resolved {
  background-color: #aaccff;
  border: none;
}

.row-done-cbb {
  background-color: #aaccff;
  border: none;
}

.row-testing {
  background-color: #c6ddff;
  border: none;
}

.row-need-eg {
  background-color: #ffc7c0;
  border: none;
}

.row-chatting {
  background-color: #ffe3c0;
  border: none;
}

.row-deferred {
  background-color: #cccccc;
  border: none;
}

.section-bar {
  background-color: #707070;
  color: #ffffff;
  border: 1px solid #404040;
}

.system-msg {
  font-family: Verdana, Helvetica, sans-serif; 
  font-size: 10pt; 
  background-color: #ffffff;
  border:  1px solid #000000;
  margin-bottom: 6px;
  margin-top: 6px;
  padding: 4px;
  width: 100%;
  color: #660033;
}

.form-title {
  font-family: Verdana, Helvetica, sans-serif; 
  font-weight: bold;
  font-size: 12pt; 
  color: #333333;
}

.form-label {
  font-family: Verdana, Helvetica, sans-serif; 
  font-weight: bold;
  font-size: 10pt; 
  color: #333333;
}

.form-optional {
  font-family: Verdana, Helvetica, sans-serif; 
  font-weight: bold;
  font-style: italic;
  font-size: 10pt; 
  color: #333333;
}

.form-element {
  font-family: Verdana, Helvetica, aans-serif;
  font-size: 10pt;
  color: #000000;
}

.form-text {
  font-family: Verdana, Helvetica, sans-serif;
  font-size: 10pt;
  color: #333333;
}

.form-mono {
  font-family: monospace;
  font-size: 12px;
  text-decoration: none;
}
"""

userDOTindex = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<tr>
    <property name="username">
        <td><display call="link('username')"></td>
    </property>
    <property name="realname">
        <td><display call="plain('realname')"></td>
    </property>
    <property name="organisation">
        <td><display call="plain('organisation')"></td>
    </property>
    <property name="address">
        <td><display call="plain('address')"></td>
    </property>
    <property name="phone">
        <td><display call="plain('phone')"></td>
    </property>
</tr>
"""

userDOTitem = """<!-- $Id: htmlbase.py,v 1.5 2001-07-30 08:12:17 richard Exp $-->
<table border=0 cellspacing=0 cellpadding=2>

<tr class="strong-header">
  <td colspan=2>Your Details</td>
</td>

<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Name</span></td>
    <td class="form-text"><display call="field('realname', size=40)"></td>
</tr>
<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Login Name</span></td>
    <td class="form-text"><display call="field('username', size=40)"></td>
</tr>
<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Login Password</span></td>
    <td class="form-text"><display call="field('password', size=10)"></td>
</tr>
<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Phone</span></td>
    <td class="form-text"><display call="field('phone', size=40)"></td>
</tr>
<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">Organisation</span></td>
    <td class="form-text"><display call="field('organisation', size=40)"></td>
</tr>
<tr  bgcolor="ffffea">
    <td width=1% nowrap align=right><span class="form-label">E-mail address</span></td>
    <td class="form-text"><display call="field('address', size=40)"></td>
</tr>

<tr bgcolor="ffffea">
    <td>&nbsp;</td>
    <td class="form-text"><display call="submit()"></td>
</tr>

<tr class="strong-header">
    <td colspan=2><b>History</b></td>
</tr>
<tr>
    <td colspan=2><display call="history()"></td>
</tr>

</table>

"""

