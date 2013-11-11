
#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"
#include "ExternalXRPInterface.h"
#include "Analyzer.h"
#include "Evaluator.h"
#include "MHProposal.h"
#include "XRPCore.h"

void *context = NULL;

void sendZMQmsg(string message,void *requester,zmq_msg_t request){
  zmq_msg_init_size (&request, message.length());
  memcpy (zmq_msg_data (&request), message.c_str(), message.length());
  zmq_msg_send (&request, requester, 0);
}

char * recvZMQmsg(void *requester) {
  zmq_msg_t reply;
  zmq_msg_init (&reply);
  int size = zmq_msg_recv (&reply, requester, 0);
  char *str = (char *) malloc (size + 1);
  memcpy (str, zmq_msg_data (&reply), size);
  str [size] = 0;
  zmq_msg_close (&reply);
  return str;
}


// Primitive__LoadRemoteXRP(host, port, xrp_name) 
shared_ptr<VentureValue> Primitive__LoadRemoteXRP::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  int port = arguments[0]->GetInteger();
  int xrp_name = arguments[1]->GetInteger();//shouled be a string - FIXME

  string url =  string("tcp://localhost:") + boost::lexical_cast<std::string>(port);
  if (context == NULL) context = zmq_ctx_new ();
  void *requester = zmq_socket (context, ZMQ_REQ);
  zmq_connect (requester, url.c_str());
  zmq_msg_t request;


  //Now server will send a bunch of data
  bool is_scorable, is_random_choice;
  int id_of_this_xrp;
  char *getreply;

  string message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name) + string(":id");
  sendZMQmsg(message,requester,request);
  getreply = recvZMQmsg(requester);
  id_of_this_xrp = atoi((char *)getreply);
  printf("%d\n",id_of_this_xrp);

  message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name)+ string(":scorable");
  sendZMQmsg(message,requester,request);
  getreply = recvZMQmsg(requester);
  is_scorable = atoi((char *)getreply);
  printf("%d\n",is_scorable);

  message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name)+ string(":rand");
  sendZMQmsg(message,requester,request);
  getreply = recvZMQmsg(requester);
  is_random_choice = atoi((char *)getreply);
  printf("%d\n",is_random_choice);

/*
  zmq_msg_t reply;
  zmq_msg_init (&reply);

  string message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name) + string(":id");
  zmq_msg_init_size (&request, message.length());
  memcpy (zmq_msg_data (&request), message.c_str(), message.length());
  zmq_msg_send (&request, requester, 0);  
  zmq_msg_recv (&reply, requester, 0);
  id_of_this_xrp = atoi((const char *)zmq_msg_data(&reply));
  printf("%d\n",id_of_this_xrp);


  message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name)+ string(":scorable");
  zmq_msg_init_size (&request, message.length());
  memcpy (zmq_msg_data (&request), message.c_str(), message.length());
  zmq_msg_send (&request, requester, 0);
  zmq_msg_recv (&reply, requester, 0);
  is_scorable = atoi((const char *)zmq_msg_data(&reply));
  printf("%d\n",is_scorable);

  message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name)+ string(":rand");
  zmq_msg_init_size (&request, message.length());
  memcpy (zmq_msg_data (&request), message.c_str(), message.length());
  zmq_msg_send (&request, requester, 0);
  zmq_msg_recv (&reply, requester, 0);
  is_random_choice = atoi((const char *)zmq_msg_data(&reply));
  printf("%d\n",is_random_choice);

  zmq_msg_close (&reply);
*/

  message = string("LoadRemoteXRP:") + boost::lexical_cast<std::string>(xrp_name)+ string(":name");
  sendZMQmsg(message,requester,request);
  getreply = recvZMQmsg(requester);
  string name ((char *)getreply);
  printf("%s\n",name.c_str());

  zmq_msg_close (&request);

  shared_ptr<XRP> new_xrp = shared_ptr<XRP>(new XRP__TemplateForExtendedXRP()); 
  dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(new_xrp)->is_scorable = is_scorable;
  dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(new_xrp)->is_random_choice = is_random_choice;
  dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(new_xrp)->name = name;
  dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(new_xrp)->socket = requester;
  dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(new_xrp)->id_of_this_xrp =id_of_this_xrp;

  return shared_ptr<VentureXRP>(new VentureXRP(new_xrp));
}
string Primitive__LoadRemoteXRP::GetName() { return "Primitive__LoadRemoteXRP"; }

void Primitive__LoadRemoteXRP::Unsampler(vector< shared_ptr<VentureValue> >& old_arguments, weak_ptr<NodeXRPApplication> caller, shared_ptr<VentureValue> sampled_value) {
  if (dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(dynamic_pointer_cast<VentureXRP>(sampled_value)->xrp)->socket == NULL) {
    return;
  }
  printf("Clearing ZMQ socket\n");
  cout << dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(dynamic_pointer_cast<VentureXRP>(sampled_value)->xrp)->socket << endl;  
  int ret = zmq_close(dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(dynamic_pointer_cast<VentureXRP>(sampled_value)->xrp)->socket);
  if (ret != 0) throw std::runtime_error("[Primitive__LoadRemoteXRP::Unsampler] ZMQ socket close was not succesful");
  dynamic_pointer_cast<XRP__TemplateForExtendedXRP>(dynamic_pointer_cast<VentureXRP>(sampled_value)->xrp)->socket = NULL; 
}



shared_ptr<VentureValue> XRP__TemplateForExtendedXRP::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() < 2) {
    throw std::runtime_error("[XRP__TemplateForExtendedXRP] Wrong number of arguments.");
  }
  //printf("Entered [[XRP__TemplateForExtendedXRP]]\n");

  string message = boost::lexical_cast<string>("TemplateForExtendedXRP:") + boost::lexical_cast<string>(this->id_of_this_xrp); //TemplateForExtendedXRP:id_of_this_xrp arg1 arg2 arg3 arg4 arg5
  for (int ii = 0; ii < arguments.size();ii++){
    message = message + ":" + boost::lexical_cast<string>(arguments[ii]->GetReal()); //these will only matter for RENDER   
  }
  zmq_msg_t request;
  zmq_msg_init_size (&request, message.length());
  memcpy (zmq_msg_data (&request), message.c_str(), message.length());
  zmq_msg_send (&request, this->socket, 0);
  zmq_msg_close (&request);

  char *getreply = recvZMQmsg(this->socket);
  int external_object_pointer = atoi((char *)getreply);

  string comp("noisyImageCompareXRP");
  //printf("-=-=-=-=-=-=-=-=-=-=-=-\n %s \n", this->name.c_str());
  if (comp.compare(this->name) == 0) {
    //printf("---------NOISY -----------%d\n",external_object_pointer);
    //printf("-=-=-=-=-=-=-=-=-=-=-=-\n" );
    return shared_ptr<VentureBoolean>(new VentureBoolean(true));
  }
  else {
    //printf("---------RENDER/LOADIMAGE-----------%d\n",external_object_pointer);
    //printf("-=-=-=-=-=-=-=-=-=-=-=-\n" );
    //return shared_ptr<VentureAtom>(new VentureAtom(external_object_pointer));
    return shared_ptr<VentureExternalXRPObject>(new VentureExternalXRPObject(external_object_pointer, this->socket));
  }
}

real XRP__TemplateForExtendedXRP::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {

  string message = boost::lexical_cast<string>("GetLogL:") + boost::lexical_cast<string>(this->id_of_this_xrp) +
                   boost::lexical_cast<string>(":") + boost::lexical_cast<string>(arguments[1]->GetString()) + 
                   boost::lexical_cast<string>(":") + boost::lexical_cast<string>(arguments[2]->GetString()); //2 contains pflip

  //printf("GETLOG: %s\n",message.c_str());
  zmq_msg_t request;
  zmq_msg_init_size (&request, message.length());
  memcpy (zmq_msg_data (&request), message.c_str(), message.length());
  zmq_msg_send (&request, this->socket, 0);
  zmq_msg_close (&request);

  zmq_msg_t reply;
  zmq_msg_init (&reply);
  int size = zmq_msg_recv (&reply, this->socket, 0);
  char *string = (char *) malloc (size + 1);
  memcpy (string, zmq_msg_data (&reply), size);
  string [size] = 0;
  float logL = atof((char *)string);
  //printf("%s| LOGL: %s\n",this->name.c_str(), string);
  zmq_msg_close (&reply);

  return logL;
}

void XRP__TemplateForExtendedXRP::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {

}

void XRP__TemplateForExtendedXRP::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
}
bool XRP__TemplateForExtendedXRP::IsRandomChoice() { return this->is_scorable; }
bool XRP__TemplateForExtendedXRP::CouldBeRescored() { return this->is_random_choice; }
string XRP__TemplateForExtendedXRP::GetName() { return this->name; }
