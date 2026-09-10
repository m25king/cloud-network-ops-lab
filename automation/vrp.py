"""Parse the explicitly supported VRP interface table, flag unknown output honestly."""
import re

ROW=re.compile(r'^\s*(\S+)\s+(?:(?:[0-9a-fA-F:./]+|unassigned)\s+)?(\*?down|up|Administratively\s+DOWN)\s+(down|up)\b',re.I)

def interfaces(text):
    rows=[]
    for line in text.splitlines():
        match=ROW.match(line)
        if match:
            name,physical,protocol=match.groups()
            rows.append({'name':name,'physical':physical.lower(),'protocol':protocol.lower(),
                         'up':physical.lower()=='up' and protocol.lower()=='up'})
    return {'parse_state':'parsed' if rows else 'unknown_format','interfaces':rows}

def evaluate(text,expected_up):
    result=interfaces(text)
    index={r['name']:r for r in result['interfaces']}
    result['missing_expected']=[n for n in expected_up if n not in index]
    result['unexpected_down']=[n for n in expected_up if n in index and not index[n]['up']]
    result['ok']=result['parse_state']=='parsed' and not result['missing_expected'] and not result['unexpected_down']
    return result

def redact_config(text):
    # Whole-line masking intentionally over-redacts rather than preserving secret substrings.
    sensitive=re.compile(r'password|cipher|secret|community|private-key|public-key-code|authentication-key|snmp-agent|local-user|ssh user|user-name|radius-server|hwtacacs-server',re.I)
    return '\n'.join('# REDACTED sensitive configuration' if sensitive.search(line) else line for line in text.splitlines())+'\n'
