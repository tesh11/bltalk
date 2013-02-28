import re

from django.db.backends import BaseDatabaseOperations


class DatabaseOperations(BaseDatabaseOperations):
#    compiler_module = "vertica.pyodbc.compiler"
    def __init__(self, connection):
        super(DatabaseOperations, self).__init__(connection)
        self._vertica_ver = None

    VERSION_RE = re.compile(r'\S+ v(\d+)\.(\d+)\.?(\d+)?-(\d+)')
    def _parse_ver(self, text):
        try:
            major, major2, minor, build = VERSION_RE.search(text).groups()
            return int(major), int(major2), int(minor)
        except (ValueError, TypeError):
            return int(major), int(major2), None

    def _get_sql_server_ver(self, connection=None):
        """
        Returns the version of the SQL Server in use:
        """
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        self._vertica_ver = self._parse_ver(cursor.fetchone()[0])
        return self._vertica_ver


    vertica_ver = property(_get_sql_server_ver)

    def date_extract_sql(self, lookup_type, field_name):
        """
        Given a lookup_type of 'year', 'month', 'day' or 'week_day', returns
        the SQL that extracts a value from the given date field field_name.
        """
        if lookup_type == 'week_day':
            # For consistency across backends, we return Sunday=1, Saturday=7.
            return "EXTRACT('dow' FROM %s) + 1" % field_name
        else:
            return "EXTRACT('%s' FROM %s)" % (lookup_type, field_name)

    def date_trunc_sql(self, lookup_type, field_name):
        """
        Given a lookup_type of 'year', 'month' or 'day', returns the SQL that
        truncates the given date field field_name to a DATE object with only
        the given specificity.
        """
        return "DATE_TRUNC ( %s , %s)" % (lookup_type, field_name)


    def fulltext_search_sql(self, field_name):
        """
        Returns the SQL WHERE clause to use in order to perform a full-text
        search of the given field_name. Note that the resulting string should
        contain a '%s' placeholder for the value being searched against.
        """
        return 'POSITION ( %%s IN %s)' % field_name

    def last_insert_id(self, cursor, table_name, pk_name):
        """
        Given a cursor object that has just performed an INSERT statement into
        a table that has an auto-incrementing ID, returns the newly created ID.

        This method also receives the table name and the name of the primary-key
        column.
        """
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()[0]
        if not result:
            seq_name = cursor.execute("selECT SPLIT_PART(column_default,'''',2) from columns where table_name=%s and column_name=%s",
                           (table_name, pk_name)).fetchone()[0]
            result = cursor.execute("select currval(%s)", (seq_name,)).fetchone()[0]
        return result

    def no_limit_value(self):
        return None

    def quote_name(self, name):
        if name.startswith('"') and name.endswith('"'):
            return name # Quoting once is enough.
        return '"%s"' % name

    def last_executed_query(self, cursor, sql, params):
        """
        Returns a string of the query last executed by the given cursor, with
        placeholders replaced with actual values.

        `sql` is the raw query containing placeholders, and `params` is the
        sequence of parameters. These are used by default, but this method
        exists for database backends to provide a better implementation
        according to their own quoting schemes.
        """
        return super(DatabaseOperations, self).last_executed_query(cursor, cursor.last_sql, cursor.last_params)

    def sql_flush(self, style, tables, sequences):
        """
        Returns a list of SQL statements required to remove all data from
        the given database tables (without actually removing the tables
        themselves).

        The `style` argument is a Style object as returned by either
        color_style() or no_style() in django.core.management.color.
        """
        if tables:
            if self.postgres_version[0:2] >= (8, 1):
                # Postgres 8.1+ can do 'TRUNCATE x, y, z...;'. In fact, it *has to*
                # in order to be able to truncate tables referenced by a foreign
                # key in any other table. The result is a single SQL TRUNCATE
                # statement.
                sql = ['%s %s;' % \
                    (style.SQL_KEYWORD('TRUNCATE'),
                     style.SQL_FIELD(', '.join([self.quote_name(table) for table in tables]))
                )]
                # 'ALTER SEQUENCE sequence_name RESTART WITH 1;'... style SQL statements
            # to reset sequence indices
            for sequence_info in sequences:
                table_name = sequence_info['table']
                column_name = sequence_info['column']
                if column_name and len(column_name) > 0:
                    sequence_name = '%s_%s_seq' % (table_name, column_name)
                else:
                    sequence_name = '%s_id_seq' % table_name
                sql.append("%s setval('%s', 1, false);" % \
                    (style.SQL_KEYWORD('SELECT'),
                    style.SQL_FIELD(self.quote_name(sequence_name)))
                )
            return sql
        else:
            return []

    def sequence_reset_sql(self, style, model_list):
        from django.db import models
        output = []
        qn = self.quote_name
        for model in model_list:
            # Use `coalesce` to set the sequence for each model to the max pk value if there are records,
            # or 1 if there are none. Set the `is_called` property (the third argument to `setval`) to true
            # if there are records (as the max pk value is already in use), otherwise set it to false.
            for f in model._meta.local_fields:
                if isinstance(f, models.AutoField):
                    output.append("%s setval('%s', coalesce(max(%s), 1), max(%s) %s null) %s %s;" % \
                        (style.SQL_KEYWORD('SELECT'),
                        style.SQL_FIELD(qn('%s_%s_seq' % (model._meta.db_table, f.column))),
                        style.SQL_FIELD(qn(f.column)),
                        style.SQL_FIELD(qn(f.column)),
                        style.SQL_KEYWORD('IS NOT'),
                        style.SQL_KEYWORD('FROM'),
                        style.SQL_TABLE(qn(model._meta.db_table))))
                    break # Only one AutoField is allowed per model, so don't bother continuing.
            for f in model._meta.many_to_many:
                if not f.rel.through:
                    output.append("%s setval('%s', coalesce(max(%s), 1), max(%s) %s null) %s %s;" % \
                        (style.SQL_KEYWORD('SELECT'),
                        style.SQL_FIELD(qn('%s_id_seq' % f.m2m_db_table())),
                        style.SQL_FIELD(qn('id')),
                        style.SQL_FIELD(qn('id')),
                        style.SQL_KEYWORD('IS NOT'),
                        style.SQL_KEYWORD('FROM'),
                        style.SQL_TABLE(qn(f.m2m_db_table()))))
        return output


    def savepoint_create_sql(self, sid):
        return "SAVEPOINT %s" % sid

    def savepoint_commit_sql(self, sid):
        return "RELEASE SAVEPOINT %s" % sid

    def savepoint_rollback_sql(self, sid):
        return "ROLLBACK TO SAVEPOINT %s" % sid


    def prep_for_iexact_query(self, x):
        """
        Same as prep_for_like_query(), but called for "iexact" matches, which
        need not necessarily be implemented using "LIKE" in the backend.
        """
        return x


