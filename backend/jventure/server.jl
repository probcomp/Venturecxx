require("engine.jl")
using JSON

function VentureServer(port::Int = 2000)
  @async begin
    server = listen(port)
    while true
      sock = accept(server)

      @async begin
        sivm = Engine()
        while true
          directive = readuntil(sock,"#")[1:end-1]
          handleDirective(sock,sivm,JSON.parse(directive))
        end
      end
    end
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
         "report_value" => report_value,
         "infer" => infer,
         "reset" => reset,
        }
  result = ops[directive[1]](sivm,directive[2:end]...)
  write(sock,json(result))
end
