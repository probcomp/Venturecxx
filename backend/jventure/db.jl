type DB
  values::Dict{Node,VentureValue}
  spFamilyDBs::Dict{(SP,SPFamilyID),Node}
end

DB() = DB((Node=>VentureValue)[],((SP,SPFamilyID)=>Node)[])

hasValue(db::DB,node::Node) = haskey(db.values,node)
getValue(db::DB,node::Node) = db.values[node]

function extractValue(db::DB,node::Node,value::VentureValue)
  @assert !haskey(db.values,node)
  db.values[node] = value
end

getSPFamilyRoot(db::DB,sp::SP,id::SPFamilyID) = db.spFamilyDBs[(sp,id)]

function registerSPFamilyRoot!(db::DB,sp::SP,id::SPFamilyID,esrParent::Node)
  @assert !haskey(db.spFamilyDBs,(sp,id))
  db.spFamilyDBs[(sp,id)] = esrParent
end

function disp(db::DB)
  println("Displaying DB")
  for (node,value) = db.values
    println(value)
  end
end