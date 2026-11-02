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

from . import models
from . import wizard


def _post_init_set_is_notify_approval_cancel(cr):
    """Set is_notify_approval_cancel to False on install"""
    cr['ir.config_parameter'].sudo().set_param(
        'all_in_one_dynamic_approvals_pro.is_notify_approval_cancel',
        False)
    cr['ir.config_parameter'].sudo().set_param(
            'all_in_one_dynamic_approvals_pro.is_notify_approval_add',
            False)
