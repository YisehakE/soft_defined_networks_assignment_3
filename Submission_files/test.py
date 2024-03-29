

import sys


def getPolicyContent(contents):
  n_rules = int(contents[0])
  m_hosts = int(contents[1])

  rules = contents[2:2 + n_rules]
  hosts = contents[2 + n_rules:]

  return n_rules, m_hosts, rules, hosts
      

policy_f = open(sys.argv[1],"r")
policy_contents = policy_f.read().split()
n_rules, m_hosts, rules, hosts = getPolicyContent(policy_contents)

print("N =  ", n_rules)
print("M =  ", m_hosts)
print("rules: ", str(rules))
print("hosts: ", str(hosts))
