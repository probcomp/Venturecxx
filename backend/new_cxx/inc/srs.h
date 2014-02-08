#ifndef SRS_H
#define SRS_H

struct ESR
{
  ESR(FamilyID id,VentureValuePtr exp,VentureEnvironmentPtr env);
  FamilyID id;
  VentureValuePtr exp;
  VentureEnvironmentPtr env;
};

struct LSR { virtual ~LSR() {} };

struct VentureRequest : VentureValue
{
  VentureRequest(const vector<ESR> & esrs, const vector<LSR*> & lsrs);
  vector<ESR> esrs;
  vector<LSR*> lsrs;
};



#endif
