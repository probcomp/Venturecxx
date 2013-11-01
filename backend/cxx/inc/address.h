#ifndef ADDRESS_H
#define ADDRESS_H

#include <string>
#include <cassert>
#include <iostream>

struct Address
{
  Address(): Address(Address::nullAddress) { }

  Address(std::string s): address(s) {}

  Address(const Address & a) = default;

  /* Hacky -- used so that the empty environment can have the same
     fields as an extended environment. */
  static const Address nullAddress;
  static const Address emptyEnvironmentAddress;
  static const Address primitivesEnvironmentAddress;
  static const Address globalEnvironmentAddress;
  
  static Address makeCSRAddress(const Address & spAddress, std::string requestedName)
  { return spAddress.addToAddress("!" + requestedName); } 

  Address addToAddress(std::string s) const
  { return Address(toString() + s); }
       
  Address getFamilyEnvAddress() const 
  { return addToAddress("#familyEnv"); } 

  Address getRequestAddress() const 
  { return addToAddress("#request"); }

  Address getOperatorAddress() const 
  { return addToAddress("#operator"); }

  Address getOperandAddress(int i) const 
  { return addToAddress("#operand" + std::to_string(i)); }

  std::string toString() const { return address; }

  bool operator==(const Address &other) const
  { return toString() == other.toString(); } 

private:
  std::string address;
};

/* For the unordered_map. When we switch to rolling hash, we will need to 
   encapsulate these in an object and pass it explicitly. */
namespace std {

  template <>
  struct hash<Address>
  {
    std::size_t operator()(const Address& a) const
    {
      using std::size_t;
      using std::hash;
      using std::string;

      return hash<string>()(a.toString());
    }
  };
}

#endif
