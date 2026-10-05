import unittest
from check_deployment_scope import errors

class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.m={'new_posts':[56,57,58,59,60],'changed_features':[{'path':'posts/theory/055-radioactive-equilibrium.html','feature':'next link','reason':'link newly published056'}]}
        self.r={k:[{'post':n,'status':'PASS'} for n in self.m['new_posts']] for k in ['articles','listing','image_url_views']}
    def test_new_only(self):self.assertEqual(errors(self.m,56,60,self.r),[])
    def test_old_full_ci_rejected(self):self.assertTrue(errors(self.m,1,60))
    def test_old_mobile_rejected(self):
        self.r['articles'].append({'post':1,'status':'PASS'});self.assertTrue(errors(self.m,56,60,self.r))
    def test_missing_new_image_rejected(self):
        self.r['image_url_views'].pop();self.assertTrue(errors(self.m,56,60,self.r))
    def test_old_http_rejected(self):self.assertTrue(errors(self.m,56,60,http={'files':{'posts/theory/001-atom.html':{'status':'PASS'}}}))
    def test_changed_link_http_allowed(self):self.assertEqual(errors(self.m,56,60,http={'files':{self.m['changed_features'][0]['path']:{'status':'PASS'}}}),[])
    def test_failure_rejected(self):
        self.r['listing'][0]['status']='FAIL';self.assertTrue(errors(self.m,56,60,self.r))

if __name__=='__main__':unittest.main()
