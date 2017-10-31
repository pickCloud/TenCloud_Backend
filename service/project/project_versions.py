from service.base import BaseService
from tornado.gen import coroutine

from constant import FULL_DATE_FORMAT

class ProjectVersionService(BaseService):
    table  = 'project_versions'
    fields = 'id, name, version, log'

    @coroutine
    def version_list(self, prj_name):
        sql = """
                SELECT v.id, v.name, v.version, DATE_FORMAT(v.update_time, %s) AS update_time, p.image_source
                FROM project_versions v JOIN project p USING(name)
                WHERE v.name=%s
                ORDER BY v.update_time DESC
              """
        cur = yield self.db.execute(sql, [FULL_DATE_FORMAT, prj_name])
        return cur.fetchall()
