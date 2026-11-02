# -*- coding: utf-8 -*-
######################################################################################
#
#    Keffah Solutions the Est. Information technology and Communication  Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Keffah Solutions the Est. Information technology and Communication Pvt. Ltd
#    (<https://www.kascco.sa>).
#    Author: Keffah Solutions the Est. Information technology and Communication Pvt. Ltd (Contact : itcs@kascco.sa)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import fields, models


class ModelData(models.Model):
    """Created model.data model purposed for storing related used in add
    dynamic approval, remove approval and create approvals"""
    _name = 'model.data'
    _rec_name = 'rec_name'

    rec_name = fields.Char(string="Name", help='Record name')
    rec_id = fields.Char(string="Id", help='Id of records if they have')
    approval_type = fields.Selection([('add', 'Add'),
                                      ('cancel', 'Cancel')], help='Data '
                                                                  'stored '
                                                                  'related to '
                                                                  'cancel or '
                                                                  'add '
                                                                  'approval')
    save = fields.Boolean(help='Whether the data is saved')
    stage_id = fields.Boolean(help='Is data related to stage_id')
    is_field = fields.Boolean(
        help='Is data related to fields used in approvals')
