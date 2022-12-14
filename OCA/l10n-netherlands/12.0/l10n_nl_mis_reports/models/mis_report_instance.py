# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import copy
from collections import OrderedDict

from odoo import api, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    @api.multi
    def compute(self):
        if not self._is_horizontal():
            return super().compute()

        full_matrix = self._compute_matrix()

        matrices = self._compute_horizontal_matrices(full_matrix)

        result = full_matrix.as_dict()
        result["horizontal_matrices"] = [
            extra_matrix.as_dict() for extra_matrix in matrices
        ]

        return result

    @api.multi
    def _is_horizontal(self):
        """Determine if the report template is a horizontal one"""
        self.ensure_one()
        return set(self.report_id.get_external_id().values()) & {
            "l10n_nl_mis_reports.report_bs",
            "l10n_nl_mis_reports.report_pl",
        }

    @api.multi
    def _compute_horizontal_matrices(self, matrix=None):
        """Compute the matrix (if not passed) and return the split versions"""
        return self._split_matrix(
            matrix or self._compute_matrix(),
            [
                (
                    self.env.ref("l10n_nl_mis_reports.kpi_profit"),
                    self.env.ref("l10n_nl_mis_reports.kpi_pl_to_report"),
                    self.env.ref("l10n_nl_mis_reports.kpi_assets"),
                )
            ],
        )

    @api.multi
    def _split_matrix(self, original_matrix, kpi_defs=None, keep_remaining=True):
        """Split a matrix by duplicating it as shallowly as possible and removing
        rows according to kpi_defs

        KPIs not listed there will end up together in the last matrix if
        `keep_remaining` is set.

        :param kpi_defs: [(kpi_first_matrix1, ...), (kpi_second_matrix1, ...)]
        :return: list of KpiMatrix
        """
        result = []
        remaining_rows = original_matrix._kpi_rows.copy()

        for kpis in kpi_defs:
            matrix = copy.copy(original_matrix)
            matrix._kpi_rows = OrderedDict(
                [
                    (kpi, remaining_rows.pop(kpi))
                    for kpi in kpis
                    if kpi in remaining_rows
                ]
            )
            result.append(matrix)

        if remaining_rows and keep_remaining:
            matrix = copy.copy(original_matrix)
            matrix._kpi_rows = remaining_rows
            result.append(matrix)

        return result
