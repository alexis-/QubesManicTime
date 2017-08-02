USG_ACTIVE = 1
USG_AWAY = 2
USG_SS_ON = 3

USG = {}
USG[USG_ACTIVE] = {}
USG[USG_ACTIVE]['displayName'] = 'Active'
USG[USG_ACTIVE]['color'] = '58C10C'
USG[USG_ACTIVE]['skipColor'] = False,
USG[USG_ACTIVE]['groupId'] = str(USG_ACTIVE)
USG[USG_ACTIVE]['displayKey'] = 'ManicTime/Active'
USG[USG_AWAY] = {}
USG[USG_AWAY]['displayName'] = 'Away'
USG[USG_AWAY]['color'] = 'F61500'
USG[USG_AWAY]['skipColor'] = False,
USG[USG_AWAY]['groupId'] = str(USG_AWAY)
USG[USG_AWAY]['displayKey'] = 'ManicTime/Away'
USG[USG_SS_ON] = {}
USG[USG_SS_ON]['displayName'] = 'Session lock'
USG[USG_SS_ON]['color'] = 'F61500'
USG[USG_SS_ON]['skipColor'] = False,
USG[USG_SS_ON]['groupId'] = str(USG_SS_ON)
USG[USG_SS_ON]['displayKey'] = 'ManicTime/SessionLocked'

USG_GROUPS = [USG[USG_ACTIVE], USG[USG_AWAY], USG[USG_SS_ON]]
