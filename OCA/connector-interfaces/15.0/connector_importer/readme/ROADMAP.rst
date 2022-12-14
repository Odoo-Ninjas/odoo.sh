* with the import of standard Odoo CSV files, a concurrency error occurs
  when updating the `report_data` of `import_recordset` table (from the
  importer: `self._do_report()` -> `self.recordset.set_report(...)`).
  The job is automatically retried a second time (without concurrency errors).
  For small files it's not a big issue, but for files with a huge amount of
  lines it takes time to process them two times.
* refactor the `recordset.full_report_url` field to return a QWeb report
  instead of a home-made HTML document + display it on the recordset form.
* move generic functions from `utils.mapper_utils` to the `connector` module
* unit tests for record handler and tracker
* add more test coverage for mapper utils and dynamic mapper
* consider making dynamic mapper the default one
