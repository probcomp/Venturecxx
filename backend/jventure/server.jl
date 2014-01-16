require("engine.jl")
using JSON

function VentureServer(port::Int = 2000)

  print("initializing server...")
  server = listen(port)
  println("done")

  print("waiting for connection...")
  sock = accept(server)
  println("done")

  print("initializing SIVM...")
  sivm = Engine()
  println("done")

  while true
    println("waiting for directive...")
    directive = readuntil(sock,"#")[1:end-1]
    println("received directive: " * directive)
    handleDirective(sock,sivm,JSON.parse(directive))
  end
  
end

# False is not ideal -- the strings "sp" and "node" probably more appropriate
JSON.print(io::IO, s::SPRef) = print(io,false)
JSON.print(io::IO, n::Node) = print(io,false)

function handleDirective(sock,sivm::Engine,directive::Array) 
  ops = { 
         "assume" => assume, 
         "predict" => predict, 
         "observe" => observe,
         "report" => report,
         "infer" => infer,
#         "reboot" => reboot,
        }
  result = ops[directive[1]](sivm,directive[2:end]...)
  write(sock,json(result))
end
