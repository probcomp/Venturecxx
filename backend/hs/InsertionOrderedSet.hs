module InsertionOrderedSet where

-- A set of elements that knows the order in which they were first inserted.

-- This particular implementation is not very efficient, because it
-- retains placeholders for removed elements in order to make sure
-- that indexes of subsequent elements remain valid.  This is silly,
-- but I am not inspired to do better right now.

import qualified Data.Sequence as S
import qualified Data.Map as M
import qualified Data.Foldable as F
import Data.Maybe

-- Representation invariants:
-- - The seq holds elements in the order in which they were first inserted
-- - The keys of the map are exactly the non-Nothing contents of the seq
-- - Each value of the map is the index of its key in the seq
--   (which is Non-Nothing at that index)
-- - The seq may hold Nothings as placeholders to make sure that map
--   values remain valid even under deletions.

data Set v = Set { insertions :: S.Seq (Maybe v)
                 , indexes :: M.Map v Int
                 }

empty :: Set v
empty = Set S.empty M.empty

insert :: (Ord v) => v -> Set v -> Set v
insert v s@Set{insertions = ins, indexes = ind} = 
    case M.lookup v ind of
      Nothing -> Set ins' ind'
      (Just _) -> s
    where new_index = S.length ins
          ins' = ins S.|> (Just v)
          ind' = M.insert v new_index ind

-- In the order in which they were first inserted
toList :: Set v -> [v]
toList = catMaybes . F.toList . insertions

delete :: (Ord v) => v -> Set v -> Set v
delete v s@Set{insertions = ins, indexes = ind} =
    case M.lookup v ind of
      Nothing -> s
      (Just oldInd) -> Set ins' ind'
          where ins' = S.update oldInd Nothing ins
                ind' = M.delete v ind
    
member :: (Ord v) => v -> Set v -> Bool
member v Set{indexes = ind} = isJust $ M.lookup v ind

instance (Show v) => Show (Set v) where
    show Set{ insertions = is } = show $ S.fromList $ catMaybes $ F.toList is
