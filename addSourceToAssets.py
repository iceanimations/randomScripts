import sys
sys.path.append(r'd:\talha.ahmed\workspace\pyenv_common\southpaw-tactic\src\client')

import tactic_client_lib
stub = tactic_client_lib.TacticServerStub.get(setup=False)

ticket='3cc3886e61bbdf9afeda4acd089ed8d0'
stub.set_ticket(ticket)
stub.set_server('dbserver')
stub.set_project('mansour_s02')


sk = '__search_key__'
context = 'sources'


def addSourceFolder(asset):
    #newss = stub.create_snapshot( asset[sk], context='sources' )
    #stub.add_file( newss['code'], file_path=r'd:\test.txt', file_type='txt',
            #mode='copy' )
    #stub.delete_sobject( newss[sk], True)
    stub.get_virtual_snapshot_path(asset[sk], context, file_type='txt',
            file_name='test.text', mkdirs=True)


if __name__ == '__main__':
    assets = stub.query('vfx/asset', columns=['code'])
    total = len(assets)
    for i, asset in enumerate(assets):
        try:
            addSourceFolder(asset)
        except BaseException as e:
            print e
        print "%s: %d of %d" % (asset['code'], i+1, total)
