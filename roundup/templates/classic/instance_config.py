#
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
# This module is free software, and you may redistribute it and/or modify
# under the same terms as Python, so long as this copyright message and
# disclaimer are retained in their original form.
#
# IN NO EVENT SHALL BIZAR SOFTWARE PTY LTD BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING
# OUT OF THE USE OF THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# BIZAR SOFTWARE PTY LTD SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS"
# BASIS, AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
# SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
# 
# $Id: instance_config.py,v 1.10.2.1 2002-01-03 02:12:05 titus Exp $

import os
import roundup.config

# roundup home is this package's directory
INSTANCE_HOME=os.path.dirname(__file__)

base_config = roundup.config.load_base_config()
instances_config = base_config.load_instances_config()

try:
    instance_name = instances_config.get_instance_name(INSTANCE_HOME)
    instance_config = instances_config.load_instance_config(instance_name)

    # The SMTP mail host that roundup will use to send mail
    MAILHOST = instance_config.get('mail', 'host')
    MAIL_DOMAIN = instance_config.get('mail', 'domain')

    HTTP_HOST = instance_config.get('standalone_http', 'host')
    HTTP_PORT = instance_config.get('standalone_http', 'port')

    # This is the directory that the database is going to be stored in
    DATABASE = instance_config.get('base', 'databasedir')

    # This is the directory that the HTML templates reside in
    TEMPLATES = instance_config.get('base', 'templatedir')

    # A descriptive name for your roundup instance
    INSTANCE_NAME = instance_config.get_name()

    # The email address that mail to roundup should go to
    ISSUE_TRACKER_EMAIL = instance_config.get('base', 'email')

    # The web address that the instance is viewable at
    ISSUE_TRACKER_WEB = instance_config.get('base', 'url')

    ADMIN_EMAIL = instance_config.get('base', 'admin_email')

    # Somewhere for roundup to log stuff internally sent to stdout or stderr
    LOG = instance_config.get('base', 'log')

    # Where to place the web filtering HTML on the index page
    FILTER_POSITION = instance_config.get('base', 'filter_position')

    # Deny or allow anonymous access to the web interface
    ANONYMOUS_ACCESS = instance_config.get('base', 'anonymous_access')

    # Deny or allow anonymous users to register through the web interface
    ANONYMOUS_REGISTER = instance_config.get('base', 'anonymous_register')

    # Send nosy messages to the author of the message
    MESSAGES_TO_AUTHOR = instance_config.get('base', 'messages_to_author')

    # Where to place the email signature
    EMAIL_SIGNATURE_POSITION = instance_config.get('base', 'email_signature_position')
except:                                 # probably in init
    DATABASE = None
    TEMPLATES = None
    ADMIN_EMAIL = ''
    
    MAILHOST = MAIL_DOMAIN = None
    HTTP_HOST = HTTP_PORT = None

    INSTANCE_NAME = None
    ISSUE_TRACKER_EMAIL = None

    ISSUE_TRACKER_WEB = None

    LOG = None

    FILTER_POSITION = None

    ANONYMOUS_ACCESS = ANONYMOUS_REGISTER = MESSAGES_TO_AUTHOR = None

    EMAIL_SIGNATURE_POSITION = None

def get_default_database_dir():
    return INSTANCE_HOME + '/db'

def get_default_admin_email():
    return base_config.get('base', 'admin_email')

#
# $Log: not supported by cvs2svn $
# Revision 1.10  2001/11/26 22:55:56  richard
# Feature:
#  . Added INSTANCE_NAME to configuration - used in web and email to identify
#    the instance.
#  . Added EMAIL_SIGNATURE_POSITION to indicate where to place the roundup
#    signature info in e-mails.
#  . Some more flexibility in the mail gateway and more error handling.
#  . Login now takes you to the page you back to the were denied access to.
#
# Fixed:
#  . Lots of bugs, thanks Roché and others on the devel mailing list!
#
# Revision 1.9  2001/10/30 00:54:45  richard
# Features:
#  . #467129 ] Lossage when username=e-mail-address
#  . #473123 ] Change message generation for author
#  . MailGW now moves 'resolved' to 'chatting' on receiving e-mail for an issue.
#
# Revision 1.8  2001/10/23 01:00:18  richard
# Re-enabled login and registration access after lopping them off via
# disabling access for anonymous users.
# Major re-org of the htmltemplate code, cleaning it up significantly. Fixed
# a couple of bugs while I was there. Probably introduced a couple, but
# things seem to work OK at the moment.
#
# Revision 1.7  2001/10/22 03:25:01  richard
# Added configuration for:
#  . anonymous user access and registration (deny/allow)
#  . filter "widget" location on index page (top, bottom, both)
# Updated some documentation.
#
# Revision 1.6  2001/10/01 06:10:42  richard
# stop people setting up roundup with our addresses as default - need to
# handle this better in the init
#
# Revision 1.5  2001/08/07 00:24:43  richard
# stupid typo
#
# Revision 1.4  2001/08/07 00:15:51  richard
# Added the copyright/license notice to (nearly) all files at request of
# Bizar Software.
#
# Revision 1.3  2001/08/02 06:38:17  richard
# Roundupdb now appends "mailing list" information to its messages which
# include the e-mail address and web interface address. Templates may
# override this in their db classes to include specific information (support
# instructions, etc).
#
# Revision 1.2  2001/07/29 07:01:39  richard
# Added vim command to all source so that we don't get no steenkin' tabs :)
#
# Revision 1.1  2001/07/23 23:28:43  richard
# Adding the classic template
#
# Revision 1.1  2001/07/23 04:33:21  anthonybaxter
# split __init__.py into 2. dbinit and instance_config.
#
#
# vim: set filetype=python ts=4 sw=4 et si
#SHA: 8791edd89251ad1a57d549a52ac6eba591d6ddd1
